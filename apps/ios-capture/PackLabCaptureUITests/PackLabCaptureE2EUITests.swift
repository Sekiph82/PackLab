import XCTest

/// PL-0451 / PL-0452 end-to-end harness: the real app in the Simulator, its camera replaced
/// by the synthetic replay source (-PackLabUITestReplay), talks to a real PackLab Studio
/// receiver started by CI. Two full guided 16-wedge scans: the first pairs with a one-time
/// code typed into the manual pairing form, the second is delivered automatically after
/// Finalize with no pairing step. The receiver-side check (validate_packscan, import report
/// image counts, exactly one paired device) runs in the CI step after this test.
@MainActor
final class PackLabCaptureE2EUITests: XCTestCase {
    private var app = XCUIApplication()
    private var step = 0

    func testTwoGuidedScansPairOnceThenSyncAutomatically() throws {
        continueAfterFailure = false
        app.launchArguments = ["-PackLabUITestReplay", "-PackLabUITestReset"]
        app.launch()
        shot("launch")

        try guidedScan(named: "Replay scan 1")
        openHistory()
        tap(app.buttons["Finalize"], "Finalize scan 1")
        XCTAssertTrue(app.buttons["Send to PackLab"].waitForExistence(timeout: 60), "scan 1 did not finalize")
        shot("scan1-finalized-not-paired")

        // First delivery: not paired yet, so Send to PackLab opens the pairing form.
        tap(app.buttons["Send to PackLab"], "Send to PackLab")
        let offer = try receiverOffer()
        enter(offer.host, into: "pairing.host")
        enter(String(offer.port), into: "pairing.port", clearing: 8)
        enter(offer.receiverInstanceID, into: "pairing.receiverID")
        enter(offer.pairingID, into: "pairing.pairingID")
        enter(offer.fingerprint, into: "pairing.fingerprint")
        enter(offer.code, into: "pairing.code")
        shot("pairing-form-filled")
        tap(app.buttons["Pair manually"], "Pair manually")
        XCTAssertTrue(app.staticTexts["completed"].waitForExistence(timeout: 180), "manual transfer did not complete")
        let remembered = app.staticTexts["pairingRemembered"]
        XCTAssertTrue(remembered.waitForExistence(timeout: 10))
        shot("scan1-sent-paired")
        XCTAssertTrue(remembered.label.hasPrefix("This phone stays paired"), remembered.label)
        tap(app.buttons["Done"], "Done")
        waitForLabel(app.staticTexts["syncStatus.Replay scan 1"], equal: "Delivered to PackLab", timeout: 30)
        shot("history-scan1-delivered")
        tap(app.buttons["Close"], "Close history")

        // Second scan: Finalize alone delivers it; no pairing form appears.
        try guidedScan(named: "Replay scan 2")
        openHistory()
        tap(app.buttons["Finalize"], "Finalize scan 2")
        let status = app.staticTexts["syncStatus.Replay scan 2"]
        XCTAssertTrue(status.waitForExistence(timeout: 60), "scan 2 was not queued for automatic delivery")
        shot("scan2-queued-\(status.label)")
        XCTAssertFalse(app.textFields["pairing.code"].exists, "automatic sync must not ask to pair again")
        waitForLabel(status, equal: "Delivered to PackLab", timeout: 240)
        shot("history-scan2-delivered-automatically")
        // Clean History: only the two scans (no exports folder row) and no problem labels.
        XCTAssertFalse(app.staticTexts["Unavailable scan"].exists, "a non-session folder is listed in History")
        XCTAssertEqual(app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'Problem:'")).count, 0, "History rows report problems")
    }

    // MARK: Steps

    private func guidedScan(named name: String) throws {
        tap(app.buttons["New Scan"], "New Scan")
        let nameField = app.textFields["Package name"]
        XCTAssertTrue(nameField.waitForExistence(timeout: 10))
        nameField.tap()
        nameField.typeText(name)
        shot("\(name)-wizard")
        tap(app.buttons["Start"], "Start")
        // The protocol Form is lazy: scroll until its Continue button is materialised.
        let proceed = app.buttons["Continue"]
        XCTAssertTrue(app.staticTexts["Capture protocol"].waitForExistence(timeout: 10))
        for _ in 0..<10 where !proceed.exists { app.swipeUp() }
        shot("\(name)-protocol")
        tap(proceed, "Continue protocol")
        let center = app.buttons["setObjectCenterButton"]
        XCTAssertTrue(center.waitForExistence(timeout: 20), "scan did not start")
        shot("\(name)-started")
        // Aim the crosshair at the package base first (the replay camera may still be at
        // the previous scan's last orbit position).
        tap(app.buttons["replayNextPoseButton"], "aim at package base")
        tap(center, "Set object center")
        XCTAssertTrue(app.staticTexts["Object center set"].waitForExistence(timeout: 10), "object center was not set")
        shot("\(name)-center-set")
        let hold = app.staticTexts["Hold here — tap Manual Capture"]
        let coverage = app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'Coverage '")).firstMatch
        for wedge in 1...16 {
            tap(app.buttons["replayNextPoseButton"], "next pose \(wedge)")
            if !hold.waitForExistence(timeout: 8) {
                // Diagnostic + one retry: record what guidance shows, then move again.
                shot("\(name)-no-hold-\(wedge)")
                tap(app.buttons["replayNextPoseButton"], "next pose \(wedge) retry")
            }
            XCTAssertTrue(hold.waitForExistence(timeout: 15), "guidance did not say hold at wedge \(wedge)")
            tap(app.buttons["manualCaptureButton"], "Manual Capture \(wedge)")
            // The 2 s toast can be missed by a slow accessibility snapshot; the persistent
            // coverage summary is the evidence that this wedge was captured.
            waitForLabel(coverage, containing: wedge == 16 ? "Coverage complete" : "; \(16 - wedge) sectors missing", timeout: 30)
            shot("\(name)-capture-\(wedge)")
        }
        XCTAssertTrue(app.staticTexts["All positions covered — finish the scan in History"].waitForExistence(timeout: 10))
        shot("\(name)-all-covered")
    }

    private func openHistory() {
        tap(app.buttons["More actions"], "More")
        tap(app.buttons["History"], "History")
        XCTAssertTrue(app.navigationBars["Scan History"].waitForExistence(timeout: 10))
        shot("history")
    }

    // MARK: Helpers

    private struct Offer { let host: String; let port: Int; let receiverInstanceID: String; let pairingID: String; let fingerprint: String; let code: String }

    /// The CI receiver keeps a fresh one-time offer in this file (TEST_RUNNER_ env passthrough).
    private func receiverOffer() throws -> Offer {
        let path = try XCTUnwrap(ProcessInfo.processInfo.environment["PACKLAB_E2E_OFFER_FILE"], "PACKLAB_E2E_OFFER_FILE is not set")
        let object = try XCTUnwrap(try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: path))) as? [String: Any])
        return Offer(host: try XCTUnwrap(object["host"] as? String), port: try XCTUnwrap(object["port"] as? Int), receiverInstanceID: try XCTUnwrap(object["receiver_instance_id"] as? String), pairingID: try XCTUnwrap(object["pairing_id"] as? String), fingerprint: try XCTUnwrap(object["tls_certificate_fingerprint"] as? String), code: try XCTUnwrap(object["pairing_code"] as? String))
    }

    private func tap(_ element: XCUIElement, _ what: String) {
        XCTAssertTrue(element.waitForExistence(timeout: 20), "\(what) not found")
        element.tap()
    }

    private func enter(_ text: String, into identifier: String, clearing: Int = 0) {
        let field = app.textFields[identifier]
        XCTAssertTrue(field.waitForExistence(timeout: 10), "\(identifier) not found")
        field.tap()
        if clearing > 0 { field.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: clearing)) }
        field.typeText(text)
    }

    private func waitForLabel(_ element: XCUIElement, equal: String? = nil, containing: String? = nil, timeout: TimeInterval) {
        let predicate = equal.map { NSPredicate(format: "label == %@", $0) } ?? NSPredicate(format: "label CONTAINS %@", containing ?? "")
        let result = XCTWaiter().wait(for: [XCTNSPredicateExpectation(predicate: predicate, object: element)], timeout: timeout)
        if result != .completed {
            shot("timeout")
            XCTFail("\(element) label is '\(element.exists ? element.label : "<missing>")', expected \(equal ?? containing ?? "")")
        }
    }

    private func shot(_ name: String) {
        step += 1
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = String(format: "%03d-%@", step, name.replacingOccurrences(of: " ", with: "_"))
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
