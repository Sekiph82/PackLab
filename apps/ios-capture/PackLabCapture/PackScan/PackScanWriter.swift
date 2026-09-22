import Compression
import CryptoKit
import Foundation

/// PackLab-owned, device-agnostic PackScan package writer.
///
/// The manifest and payload bytes are supplied by the Capture service as
/// contract data. This type does not import camera, ARKit, or NextLevel APIs;
/// those remain behind the existing service boundaries. Python remains the
/// cross-platform validator and schema authority.
public struct PackScanWriter: Sendable {
    public static let schemaVersion = "1.0.0"
    public static let checksumCanonicalization = "sha256_32_bytes_lowercase_hex_64_chars_v1"

    public init() {}

    public func write(
        manifestJSON: Data,
        payloads: [String: Data],
        to destination: URL
    ) throws {
        let manifest = try canonicalJSON(manifestJSON)
        let declared = try validateManifest(manifest, payloads: payloads)
        var files: [String: Data] = ["manifest.json": manifest]
        for path in declared.sorted() {
            guard let bytes = payloads[path] else {
                throw PackScanWriterError.missingPayload(path)
            }
            files[path] = bytes
        }

        let checksums = files.reduce(into: [String: String]()) { result, entry in
            result[entry.key] = sha256(entry.value)
        }
        let index: [String: Any] = [
            "schema_version": Self.schemaVersion,
            "algorithm": "sha256",
            "canonicalization": Self.checksumCanonicalization,
            "entries": checksums,
        ]
        files["checksums.json"] = try canonicalJSON(index)
        let archive = try DeterministicZipArchive(files: files).data()
        try finalize(archive, at: destination)
    }

    private func validateManifest(_ manifest: Data, payloads: [String: Data]) throws -> Set<String> {
        guard
            let object = try JSONSerialization.jsonObject(with: manifest) as? [String: Any],
            object["schema_version"] as? String == Self.schemaVersion,
            let contract = object["checksums"] as? [String: Any],
            contract["algorithm"] as? String == "sha256",
            contract["canonicalization"] as? String == Self.checksumCanonicalization,
            let declaredPayloads = object["payloads"] as? [[String: Any]],
            declaredPayloads.count >= 2
        else {
            throw PackScanWriterError.schemaInvalid
        }

        var declared = Set<String>()
        for item in declaredPayloads {
            guard
                let path = item["path"] as? String,
                safePath(path),
                path != "manifest.json",
                path != "checksums.json",
                let size = item["size_bytes"] as? Int,
                size >= 0,
                let digest = item["sha256"] as? String,
                digest == sha256(payloads[path] ?? Data()),
                payloads[path]?.count == size,
                declared.insert(path).inserted
            else {
                throw PackScanWriterError.schemaInvalid
            }
            if let kind = item["kind"] as? String, kind == "image", !path.hasPrefix("images/") {
                throw PackScanWriterError.schemaInvalid
            }
        }
        guard declared.contains("metadata/photos.json"), declared.contains(where: { $0.hasPrefix("images/") }) else {
            throw PackScanWriterError.schemaInvalid
        }
        guard Set(payloads.keys) == declared else {
            throw PackScanWriterError.payloadSetMismatch
        }
        return declared
    }

    private func canonicalJSON(_ data: Data) throws -> Data {
        let object = try JSONSerialization.jsonObject(with: data)
        return try canonicalJSON(object)
    }

    private func canonicalJSON(_ object: Any) throws -> Data {
        var data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        data.append(0x0A)
        return data
    }

    private func safePath(_ path: String) -> Bool {
        guard !path.isEmpty, !path.hasPrefix("/"), !path.contains("\\"), !path.contains(":") else {
            return false
        }
        return !path.split(separator: "/", omittingEmptySubsequences: false).contains { $0.isEmpty || $0 == "." || $0 == ".." }
    }

    private func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    private func finalize(_ archive: Data, at destination: URL) throws {
        let fileManager = FileManager.default
        let parent = destination.deletingLastPathComponent()
        try fileManager.createDirectory(at: parent, withIntermediateDirectories: true)
        guard !fileManager.fileExists(atPath: destination.path) else {
            throw PackScanWriterError.destinationExists
        }
        let temporary = parent.appendingPathComponent(".packscan-" + UUID().uuidString + ".partial")
        do {
            try archive.write(to: temporary, options: [.atomic])
            try fileManager.moveItem(at: temporary, to: destination)
        } catch {
            try? fileManager.removeItem(at: temporary)
            throw PackScanWriterError.finalizationFailed
        }
    }
}

public enum PackScanWriterError: Error, Equatable {
    case destinationExists
    case finalizationFailed
    case missingPayload(String)
    case payloadSetMismatch
    case schemaInvalid
    case zipEncodingFailed
}

private struct DeterministicZipArchive {
    let files: [String: Data]

    func data() throws -> Data {
        let order = ["manifest.json", "metadata/photos.json", "checksums.json"] + files.keys.filter {
            !["manifest.json", "metadata/photos.json", "checksums.json"].contains($0)
        }.sorted()
        var output = Data()
        var centralDirectory = Data()
        var offsets: [String: UInt32] = [:]
        for name in order {
            guard let bytes = files[name] else { continue }
            guard let offset = UInt32(exactly: output.count) else { throw PackScanWriterError.zipEncodingFailed }
            offsets[name] = offset
            let compressed = try Deflater.deflate(bytes)
            appendLocalHeader(to: &output, name: name, bytes: bytes, compressed: compressed)
        }
        let centralOffset = output.count
        for name in order {
            guard let bytes = files[name], let offset = offsets[name] else { continue }
            let compressed = try Deflater.deflate(bytes)
            appendCentralHeader(to: &centralDirectory, name: name, bytes: bytes, compressed: compressed, offset: offset)
        }
        output.append(centralDirectory)
        appendUInt32(&output, 0x06054b50)
        appendUInt16(&output, 0)
        appendUInt16(&output, 0)
        appendUInt16(&output, UInt16(order.count))
        appendUInt16(&output, UInt16(order.count))
        appendUInt32(&output, UInt32(centralDirectory.count))
        appendUInt32(&output, UInt32(centralOffset))
        appendUInt16(&output, 0)
        return output
    }

    private func appendLocalHeader(to output: inout Data, name: String, bytes: Data, compressed: Data) {
        appendUInt32(&output, 0x04034b50); appendUInt16(&output, 20); appendUInt16(&output, 0)
        appendUInt16(&output, 8); appendUInt16(&output, 0); appendUInt16(&output, 0)
        appendUInt32(&output, CRC32.checksum(bytes)); appendUInt32(&output, UInt32(compressed.count)); appendUInt32(&output, UInt32(bytes.count))
        appendName(&output, name); output.append(compressed)
    }

    private func appendCentralHeader(to output: inout Data, name: String, bytes: Data, compressed: Data, offset: UInt32) {
        appendUInt32(&output, 0x02014b50); appendUInt16(&output, 20); appendUInt16(&output, 20); appendUInt16(&output, 0)
        appendUInt16(&output, 8); appendUInt16(&output, 0); appendUInt16(&output, 0)
        appendUInt32(&output, CRC32.checksum(bytes)); appendUInt32(&output, UInt32(compressed.count)); appendUInt32(&output, UInt32(bytes.count))
        appendName(&output, name); appendUInt16(&output, 0); appendUInt16(&output, 0); appendUInt16(&output, 0); appendUInt16(&output, 0); appendUInt32(&output, 0); appendUInt32(&output, offset)
    }

    private func appendName(_ output: inout Data, _ name: String) {
        let nameData = Data(name.utf8); appendUInt16(&output, UInt16(nameData.count)); appendUInt16(&output, 0); output.append(nameData)
    }

    private func appendUInt16(_ output: inout Data, _ value: UInt16) { output.append(UInt8(value & 0xff)); output.append(UInt8(value >> 8)) }
    private func appendUInt32(_ output: inout Data, _ value: UInt32) { appendUInt16(&output, UInt16(value & 0xffff)); appendUInt16(&output, UInt16(value >> 16)) }
}

private enum Deflater {
    static func deflate(_ data: Data) throws -> Data {
        var stream = compression_stream()
        guard compression_stream_init(&stream, COMPRESSION_STREAM_ENCODE, COMPRESSION_ZLIB) == COMPRESSION_STATUS_OK else {
            throw PackScanWriterError.zipEncodingFailed
        }
        defer { compression_stream_destroy(&stream) }
        var result = Data()
        var buffer = [UInt8](repeating: 0, count: 32_768)
        return try data.withUnsafeBytes { source in
            stream.src_ptr = source.bindMemory(to: UInt8.self).baseAddress
            stream.src_size = source.count
            var status: compression_status = COMPRESSION_STATUS_OK
            repeat {
                let before = stream.src_size
                status = buffer.withUnsafeMutableBytes { destination in
                    stream.dst_ptr = destination.bindMemory(to: UInt8.self).baseAddress
                    stream.dst_size = destination.count
                    let flags: Int32 = stream.src_size == 0 ? Int32(COMPRESSION_STREAM_FINALIZE.rawValue) : 0
                    return compression_stream_process(&stream, flags)
                }
                let written = buffer.count - stream.dst_size
                result.append(contentsOf: buffer[..<written])
                if status == COMPRESSION_STATUS_ERROR || (before == stream.src_size && written == 0 && status != COMPRESSION_STATUS_END) {
                    throw PackScanWriterError.zipEncodingFailed
                }
                if stream.src_size == 0 && status == COMPRESSION_STATUS_END { break }
            } while true
            guard result.count >= 6 else { throw PackScanWriterError.zipEncodingFailed }
            // Compression's ZLIB stream includes RFC 1950 framing; ZIP method
            // 8 stores the raw DEFLATE member, so remove the zlib header and
            // Adler-32 trailer after successful finalization.
            return Data(result.dropFirst(2).dropLast(4))
        }
    }
}

private enum CRC32 {
    static func checksum(_ data: Data) -> UInt32 {
        var crc: UInt32 = 0xffffffff
        for byte in data {
            crc ^= UInt32(byte)
            for _ in 0..<8 { crc = (crc >> 1) ^ (0xedb88320 & 0 - (crc & 1)) }
        }
        return ~crc
    }
}
