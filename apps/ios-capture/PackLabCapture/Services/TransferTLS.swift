import Foundation

#if canImport(Security)
import Security
import CryptoKit

public final class PinnedReceiverSessionDelegate: NSObject, URLSessionDelegate {
    private let expectedFingerprint: String
    public init(expectedFingerprint: String) { self.expectedFingerprint = expectedFingerprint.lowercased() }

    public func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let trust = challenge.protectionSpace.serverTrust,
              let certificate = SecTrustGetCertificateAtIndex(trust, 0),
              let data = SecCertificateCopyData(certificate) as Data?,
              let digest = Self.sha256(data),
              digest == expectedFingerprint else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        completionHandler(.useCredential, URLCredential(trust: trust))
    }

    private static func sha256(_ data: Data) -> String? {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}
#endif
