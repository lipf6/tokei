import Foundation

private enum TestFailure: Error {
    case assertion(String)
}

@main
struct KimiQuotaModelCheck {
    static func main() throws {
        let emptyRange = """
        {"hit":0,"in":0,"out":0,"cr":0,"cw":0,"reason":0,"cost":0,"sessions":0,"models":[]}
        """
        let ranges = """
        {"today":\(emptyRange),"yesterday":\(emptyRange),"week":\(emptyRange),"last_week":\(emptyRange),"month":\(emptyRange),"year":\(emptyRange)}
        """
        let current = """
        {"ranges":\(ranges),"weekly":{"used":27,"limit":100,"duration":1,"unit":"week","reset_at":200},"limits":[{"used":24,"limit":100,"duration":5,"unit":"hour","reset_at":100}],"q_source":"live","q_stale":false}
        """
        let legacy = """
        {"ranges":\(ranges)}
        """

        let decoder = JSONDecoder()
        let stat = try decoder.decode(KimiStat.self, from: Data(current.utf8))
        try expect(stat.weekly?.usedPercent == 27, "weekly quota should decode")
        try expect(stat.limits.first?.usedPercent == 24, "five-hour quota should decode")
        try expect(stat.q_source == "live", "quota source should decode")

        let legacyStat = try decoder.decode(KimiStat.self, from: Data(legacy.utf8))
        try expect(legacyStat.weekly == nil, "legacy payload should keep quota optional")
        try expect(legacyStat.limits.isEmpty, "legacy payload should default limits to empty")
        print("Kimi quota model checks passed")
    }

    private static func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
        if !condition() { throw TestFailure.assertion(message) }
    }
}
