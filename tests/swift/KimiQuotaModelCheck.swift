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

        let now = 1_000
        var missingTimestamp = legacyStat
        missingTimestamp.normalizePersistentQuota(
            now: Date(timeIntervalSince1970: TimeInterval(now))
        )
        try expect(missingTimestamp.q_stale == true, "quota without an update time should be stale")

        var fresh = try decodeStat(ranges: ranges, updated: now - 300,
                                   weeklyReset: now + 1, limitReset: now + 1)
        fresh.normalizePersistentQuota(now: Date(timeIntervalSince1970: TimeInterval(now)))
        try expect(fresh.q_source == "cache", "persistent quota should be marked as cache")
        try expect(fresh.q_stale == false, "quota at the five-minute boundary should stay fresh")

        var expiredByAge = try decodeStat(ranges: ranges, updated: now - 301,
                                          weeklyReset: now + 1, limitReset: now + 1)
        expiredByAge.normalizePersistentQuota(now: Date(timeIntervalSince1970: TimeInterval(now)))
        try expect(expiredByAge.q_stale == true, "quota older than five minutes should be stale")

        var future = try decodeStat(ranges: ranges, updated: now + 1,
                                    weeklyReset: now + 1, limitReset: now + 1)
        future.normalizePersistentQuota(now: Date(timeIntervalSince1970: TimeInterval(now)))
        try expect(future.q_stale == true, "future quota timestamps should be stale")

        var expiredWeekly = try decodeStat(ranges: ranges, updated: now,
                                           weeklyReset: now, limitReset: now + 1)
        expiredWeekly.normalizePersistentQuota(now: Date(timeIntervalSince1970: TimeInterval(now)))
        try expect(expiredWeekly.q_stale == true, "expired weekly quota should be stale")

        var expiredLimit = try decodeStat(ranges: ranges, updated: now,
                                          weeklyReset: now + 1, limitReset: now)
        expiredLimit.normalizePersistentQuota(now: Date(timeIntervalSince1970: TimeInterval(now)))
        try expect(expiredLimit.q_stale == true, "any expired limit should make quota stale")
        print("Kimi quota model checks passed: 8")
    }

    private static func decodeStat(
        ranges: String,
        updated: Int,
        weeklyReset: Int,
        limitReset: Int
    ) throws -> KimiStat {
        let json = """
        {"ranges":\(ranges),"weekly":{"used":27,"limit":100,"reset_at":\(weeklyReset)},"limits":[{"used":24,"limit":100,"reset_at":\(limitReset)}],"q_updated":\(updated),"q_source":"live","q_stale":false}
        """
        return try JSONDecoder().decode(KimiStat.self, from: Data(json.utf8))
    }

    private static func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
        if !condition() { throw TestFailure.assertion(message) }
    }
}
