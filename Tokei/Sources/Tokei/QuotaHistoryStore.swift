import Combine
import Foundation

struct QuotaModelActivity: Codable, Equatable, Identifiable {
    var model: String
    var tokenDelta: Int

    var id: String { model }
}

struct QuotaHistoryPoint: Codable, Equatable, Identifiable {
    var timestamp: Int
    var claudeFiveHourRemaining: Double?
    var claudeWeekRemaining: Double?
    var claudeFableWeekRemaining: Double?
    var codexWeekRemaining: Double?
    var grokWeekRemaining: Double?
    var kimiFiveHourRemaining: Double?
    var kimiWeekRemaining: Double?
    var claudeActivity: [QuotaModelActivity] = []
    var codexActivity: [QuotaModelActivity] = []
    var grokActivity: [QuotaModelActivity] = []
    var kimiActivity: [QuotaModelActivity] = []

    var id: Int { timestamp }

    private enum CodingKeys: String, CodingKey {
        case timestamp, claudeFiveHourRemaining, claudeWeekRemaining
        case claudeFableWeekRemaining, codexWeekRemaining, grokWeekRemaining
        case kimiFiveHourRemaining, kimiWeekRemaining
        case claudeActivity, codexActivity, grokActivity, kimiActivity
    }

    init(
        timestamp: Int,
        claudeFiveHourRemaining: Double?,
        claudeWeekRemaining: Double?,
        claudeFableWeekRemaining: Double?,
        codexWeekRemaining: Double?,
        grokWeekRemaining: Double? = nil,
        kimiFiveHourRemaining: Double? = nil,
        kimiWeekRemaining: Double? = nil,
        claudeActivity: [QuotaModelActivity] = [],
        codexActivity: [QuotaModelActivity] = [],
        grokActivity: [QuotaModelActivity] = [],
        kimiActivity: [QuotaModelActivity] = []
    ) {
        self.timestamp = timestamp
        self.claudeFiveHourRemaining = claudeFiveHourRemaining
        self.claudeWeekRemaining = claudeWeekRemaining
        self.claudeFableWeekRemaining = claudeFableWeekRemaining
        self.codexWeekRemaining = codexWeekRemaining
        self.grokWeekRemaining = grokWeekRemaining
        self.kimiFiveHourRemaining = kimiFiveHourRemaining
        self.kimiWeekRemaining = kimiWeekRemaining
        self.claudeActivity = claudeActivity
        self.codexActivity = codexActivity
        self.grokActivity = grokActivity
        self.kimiActivity = kimiActivity
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.init(
            timestamp: try container.decode(Int.self, forKey: .timestamp),
            claudeFiveHourRemaining: try container.decodeIfPresent(Double.self, forKey: .claudeFiveHourRemaining),
            claudeWeekRemaining: try container.decodeIfPresent(Double.self, forKey: .claudeWeekRemaining),
            claudeFableWeekRemaining: try container.decodeIfPresent(Double.self, forKey: .claudeFableWeekRemaining),
            codexWeekRemaining: try container.decodeIfPresent(Double.self, forKey: .codexWeekRemaining),
            grokWeekRemaining: try container.decodeIfPresent(Double.self, forKey: .grokWeekRemaining),
            kimiFiveHourRemaining: try container.decodeIfPresent(Double.self, forKey: .kimiFiveHourRemaining),
            kimiWeekRemaining: try container.decodeIfPresent(Double.self, forKey: .kimiWeekRemaining),
            claudeActivity: try container.decodeIfPresent([QuotaModelActivity].self, forKey: .claudeActivity) ?? [],
            codexActivity: try container.decodeIfPresent([QuotaModelActivity].self, forKey: .codexActivity) ?? [],
            grokActivity: try container.decodeIfPresent([QuotaModelActivity].self, forKey: .grokActivity) ?? [],
            kimiActivity: try container.decodeIfPresent([QuotaModelActivity].self, forKey: .kimiActivity) ?? []
        )
    }

    func hasTrajectory(for tool: QuotaHistoryTool) -> Bool {
        switch tool {
        case .claude:
            return claudeFiveHourRemaining != nil || claudeWeekRemaining != nil
                || claudeFableWeekRemaining != nil || !claudeActivity.isEmpty
        case .codex:
            return codexWeekRemaining != nil || !codexActivity.isEmpty
        case .grok:
            return grokWeekRemaining != nil || !grokActivity.isEmpty
        case .kimi:
            return kimiWeekRemaining != nil || kimiFiveHourRemaining != nil || !kimiActivity.isEmpty
        }
    }
}

struct QuotaCapture {
    var claudeFiveHourRemaining: Double?
    var claudeWeekRemaining: Double?
    var claudeFableWeekRemaining: Double?
    var codexWeekRemaining: Double?
    var grokWeekRemaining: Double?
    var kimiFiveHourRemaining: Double?
    var kimiWeekRemaining: Double?
    var claudeModelTotals: [String: Int]
    var codexModelTotals: [String: Int]
    var grokModelTotals: [String: Int]
    var kimiModelTotals: [String: Int]

    init(
        claudeFiveHourRemaining: Double? = nil,
        claudeWeekRemaining: Double? = nil,
        claudeFableWeekRemaining: Double? = nil,
        codexWeekRemaining: Double? = nil,
        grokWeekRemaining: Double? = nil,
        kimiFiveHourRemaining: Double? = nil,
        kimiWeekRemaining: Double? = nil,
        claudeModelTotals: [String: Int] = [:],
        codexModelTotals: [String: Int] = [:],
        grokModelTotals: [String: Int] = [:],
        kimiModelTotals: [String: Int] = [:]
    ) {
        self.claudeFiveHourRemaining = claudeFiveHourRemaining
        self.claudeWeekRemaining = claudeWeekRemaining
        self.claudeFableWeekRemaining = claudeFableWeekRemaining
        self.codexWeekRemaining = codexWeekRemaining
        self.grokWeekRemaining = grokWeekRemaining
        self.kimiFiveHourRemaining = kimiFiveHourRemaining
        self.kimiWeekRemaining = kimiWeekRemaining
        self.claudeModelTotals = claudeModelTotals
        self.codexModelTotals = codexModelTotals
        self.grokModelTotals = grokModelTotals
        self.kimiModelTotals = kimiModelTotals
    }
}

private struct QuotaHistoryState: Codable {
    var version = 1
    var points: [QuotaHistoryPoint] = []
    var lastClaudeModelTotals: [String: Int] = [:]
    var lastCodexModelTotals: [String: Int] = [:]
    var lastGrokModelTotals: [String: Int] = [:]
    var lastKimiModelTotals: [String: Int] = [:]
    var hasClaudeBaseline = false
    var hasCodexBaseline = false
    var hasGrokBaseline = false
    var hasKimiBaseline = false
    var claudeBaselineDay: Int?
    var codexBaselineDay: Int?
    var grokBaselineDay: Int?
    var kimiBaselineDay: Int?

    private enum CodingKeys: String, CodingKey {
        case version, points, lastClaudeModelTotals, lastCodexModelTotals
        case lastGrokModelTotals, lastKimiModelTotals
        case hasClaudeBaseline, hasCodexBaseline, hasGrokBaseline, hasKimiBaseline
        case claudeBaselineDay, codexBaselineDay, grokBaselineDay, kimiBaselineDay
    }

    init() {}

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        version = try container.decodeIfPresent(Int.self, forKey: .version) ?? 1
        points = try container.decodeIfPresent([QuotaHistoryPoint].self, forKey: .points) ?? []
        lastClaudeModelTotals = try container.decodeIfPresent([String: Int].self, forKey: .lastClaudeModelTotals) ?? [:]
        lastCodexModelTotals = try container.decodeIfPresent([String: Int].self, forKey: .lastCodexModelTotals) ?? [:]
        lastGrokModelTotals = try container.decodeIfPresent([String: Int].self, forKey: .lastGrokModelTotals) ?? [:]
        lastKimiModelTotals = try container.decodeIfPresent([String: Int].self, forKey: .lastKimiModelTotals) ?? [:]
        hasClaudeBaseline = try container.decodeIfPresent(Bool.self, forKey: .hasClaudeBaseline) ?? false
        hasCodexBaseline = try container.decodeIfPresent(Bool.self, forKey: .hasCodexBaseline) ?? false
        hasGrokBaseline = try container.decodeIfPresent(Bool.self, forKey: .hasGrokBaseline) ?? false
        hasKimiBaseline = try container.decodeIfPresent(Bool.self, forKey: .hasKimiBaseline) ?? false
        claudeBaselineDay = try container.decodeIfPresent(Int.self, forKey: .claudeBaselineDay)
        codexBaselineDay = try container.decodeIfPresent(Int.self, forKey: .codexBaselineDay)
        grokBaselineDay = try container.decodeIfPresent(Int.self, forKey: .grokBaselineDay)
        kimiBaselineDay = try container.decodeIfPresent(Int.self, forKey: .kimiBaselineDay)
    }
}

final class QuotaHistoryStore: ObservableObject {
    static let shared = QuotaHistoryStore()

    @Published private(set) var points: [QuotaHistoryPoint]

    private let fileURL: URL
    private let retentionSeconds: Int
    private var state: QuotaHistoryState

    init(
        fileURL: URL = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".tokei/quota_history.json"),
        retentionHours: Int = 24 * 7
    ) {
        self.fileURL = fileURL
        retentionSeconds = max(24, retentionHours) * 60 * 60
        state = Self.loadState(from: fileURL)
        points = state.points.sorted { $0.timestamp < $1.timestamp }
    }

    func record(_ capture: QuotaCapture, at date: Date = Date()) {
        let minute = Int(date.timeIntervalSince1970 / 60) * 60
        let day = Int(Calendar.current.startOfDay(for: date).timeIntervalSince1970)
        let cutoff = minute - retentionSeconds
        var changed = false

        let retained = points.filter { $0.timestamp >= cutoff }
        if retained != points {
            points = retained
            changed = true
        }

        let claudeBaseline = prepareBaseline(
            previous: state.lastClaudeModelTotals,
            hasBaseline: state.hasClaudeBaseline,
            baselineDay: state.claudeBaselineDay,
            currentDay: day
        )
        let codexBaseline = prepareBaseline(
            previous: state.lastCodexModelTotals,
            hasBaseline: state.hasCodexBaseline,
            baselineDay: state.codexBaselineDay,
            currentDay: day
        )
        let grokBaseline = prepareBaseline(
            previous: state.lastGrokModelTotals,
            hasBaseline: state.hasGrokBaseline,
            baselineDay: state.grokBaselineDay,
            currentDay: day
        )
        let kimiBaseline = prepareBaseline(
            previous: state.lastKimiModelTotals,
            hasBaseline: state.hasKimiBaseline,
            baselineDay: state.kimiBaselineDay,
            currentDay: day
        )
        let claudeActivity = activity(
            current: capture.claudeModelTotals,
            previous: claudeBaseline.previous,
            hasBaseline: claudeBaseline.hasBaseline
        )
        let codexActivity = activity(
            current: capture.codexModelTotals,
            previous: codexBaseline.previous,
            hasBaseline: codexBaseline.hasBaseline
        )
        let grokActivity = activity(
            current: capture.grokModelTotals,
            previous: grokBaseline.previous,
            hasBaseline: grokBaseline.hasBaseline
        )
        let kimiActivity = activity(
            current: capture.kimiModelTotals,
            previous: kimiBaseline.previous,
            hasBaseline: kimiBaseline.hasBaseline
        )

        let nextClaudeBaseline = updatedBaseline(
            current: capture.claudeModelTotals,
            prepared: claudeBaseline,
            existingDay: state.claudeBaselineDay,
            currentDay: day
        )
        state.lastClaudeModelTotals = nextClaudeBaseline.totals
        state.hasClaudeBaseline = nextClaudeBaseline.hasBaseline
        state.claudeBaselineDay = nextClaudeBaseline.day

        let nextCodexBaseline = updatedBaseline(
            current: capture.codexModelTotals,
            prepared: codexBaseline,
            existingDay: state.codexBaselineDay,
            currentDay: day
        )
        state.lastCodexModelTotals = nextCodexBaseline.totals
        state.hasCodexBaseline = nextCodexBaseline.hasBaseline
        state.codexBaselineDay = nextCodexBaseline.day

        let nextGrokBaseline = updatedBaseline(
            current: capture.grokModelTotals,
            prepared: grokBaseline,
            existingDay: state.grokBaselineDay,
            currentDay: day
        )
        state.lastGrokModelTotals = nextGrokBaseline.totals
        state.hasGrokBaseline = nextGrokBaseline.hasBaseline
        state.grokBaselineDay = nextGrokBaseline.day

        let nextKimiBaseline = updatedBaseline(
            current: capture.kimiModelTotals,
            prepared: kimiBaseline,
            existingDay: state.kimiBaselineDay,
            currentDay: day
        )
        state.lastKimiModelTotals = nextKimiBaseline.totals
        state.hasKimiBaseline = nextKimiBaseline.hasBaseline
        state.kimiBaselineDay = nextKimiBaseline.day

        let incoming = QuotaHistoryPoint(
            timestamp: minute,
            claudeFiveHourRemaining: normalized(capture.claudeFiveHourRemaining),
            claudeWeekRemaining: normalized(capture.claudeWeekRemaining),
            claudeFableWeekRemaining: normalized(capture.claudeFableWeekRemaining),
            codexWeekRemaining: normalized(capture.codexWeekRemaining),
            grokWeekRemaining: normalized(capture.grokWeekRemaining),
            kimiFiveHourRemaining: normalized(capture.kimiFiveHourRemaining),
            kimiWeekRemaining: normalized(capture.kimiWeekRemaining),
            claudeActivity: claudeActivity,
            codexActivity: codexActivity,
            grokActivity: grokActivity,
            kimiActivity: kimiActivity
        )

        let hasUsefulData = incoming.claudeFiveHourRemaining != nil ||
            incoming.claudeWeekRemaining != nil ||
            incoming.claudeFableWeekRemaining != nil ||
            incoming.codexWeekRemaining != nil ||
            incoming.grokWeekRemaining != nil ||
            incoming.kimiFiveHourRemaining != nil ||
            incoming.kimiWeekRemaining != nil ||
            !incoming.claudeActivity.isEmpty ||
            !incoming.codexActivity.isEmpty ||
            !incoming.grokActivity.isEmpty ||
            !incoming.kimiActivity.isEmpty

        if hasUsefulData {
            if let lastIndex = points.indices.last, points[lastIndex].timestamp == minute {
                let merged = merge(points[lastIndex], with: incoming)
                if merged != points[lastIndex] {
                    points[lastIndex] = merged
                    changed = true
                }
            } else {
                points.append(incoming)
                changed = true
            }
        }

        if changed || nextClaudeBaseline.changed || nextCodexBaseline.changed
            || nextGrokBaseline.changed || nextKimiBaseline.changed {
            state.points = points
            saveState()
        }
    }

    func points(since date: Date) -> [QuotaHistoryPoint] {
        let cutoff = Int(date.timeIntervalSince1970)
        return points.filter { $0.timestamp >= cutoff }
    }

    private static func loadState(from fileURL: URL) -> QuotaHistoryState {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return QuotaHistoryState()
        }
        do {
            let data = try Data(contentsOf: fileURL)
            let decoded = try JSONDecoder().decode(QuotaHistoryState.self, from: data)
            guard decoded.version == 1 else {
                fputs("Tokei quota history version is unsupported: \(decoded.version)\n", stderr)
                return QuotaHistoryState()
            }
            return decoded
        } catch {
            fputs("Tokei quota history load failed: \(error)\n", stderr)
            return QuotaHistoryState()
        }
    }

    private func saveState() {
        let directory = fileURL.deletingLastPathComponent()
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let data = try JSONEncoder().encode(state)
            try data.write(to: fileURL, options: .atomic)
            try? FileManager.default.setAttributes(
                [.posixPermissions: 0o600],
                ofItemAtPath: fileURL.path
            )
        } catch {
            fputs("Tokei quota history write failed: \(error)\n", stderr)
        }
    }

    private func normalized(_ value: Double?) -> Double? {
        guard let value, value.isFinite else { return nil }
        return min(100, max(0, value))
    }

    private func activity(
        current: [String: Int],
        previous: [String: Int],
        hasBaseline: Bool
    ) -> [QuotaModelActivity] {
        guard hasBaseline else { return [] }
        return current.compactMap { model, total in
            let delta = total - (previous[model] ?? 0)
            guard delta > 0 else { return nil }
            return QuotaModelActivity(model: model, tokenDelta: delta)
        }.sorted {
            if $0.tokenDelta == $1.tokenDelta { return $0.model < $1.model }
            return $0.tokenDelta > $1.tokenDelta
        }
    }

    private func prepareBaseline(
        previous: [String: Int],
        hasBaseline: Bool,
        baselineDay: Int?,
        currentDay: Int
    ) -> (previous: [String: Int], hasBaseline: Bool, dayChanged: Bool) {
        let dayChanged = baselineDay != nil && baselineDay != currentDay
        if dayChanged {
            return ([:], false, true)
        }
        return (previous, hasBaseline, false)
    }

    private func updatedBaseline(
        current: [String: Int],
        prepared: (previous: [String: Int], hasBaseline: Bool, dayChanged: Bool),
        existingDay: Int?,
        currentDay: Int
    ) -> (totals: [String: Int], hasBaseline: Bool, day: Int?, changed: Bool) {
        // A successful top-level refresh can still contain an empty tool range when one
        // scanner fails. Preserve a non-empty same-day baseline so recovery does not
        // attribute the whole day to one minute.
        let shouldReplace = prepared.dayChanged || !prepared.hasBaseline ||
            !current.isEmpty || prepared.previous.isEmpty
        guard shouldReplace else {
            return (prepared.previous, prepared.hasBaseline, existingDay, false)
        }
        let changed = prepared.previous != current ||
            !prepared.hasBaseline || existingDay != currentDay
        return (current, true, currentDay, changed)
    }

    private func merge(
        _ existing: QuotaHistoryPoint,
        with incoming: QuotaHistoryPoint
    ) -> QuotaHistoryPoint {
        var merged = existing
        merged.claudeFiveHourRemaining =
            incoming.claudeFiveHourRemaining ?? existing.claudeFiveHourRemaining
        merged.claudeWeekRemaining =
            incoming.claudeWeekRemaining ?? existing.claudeWeekRemaining
        merged.claudeFableWeekRemaining =
            incoming.claudeFableWeekRemaining ?? existing.claudeFableWeekRemaining
        merged.codexWeekRemaining =
            incoming.codexWeekRemaining ?? existing.codexWeekRemaining
        merged.grokWeekRemaining =
            incoming.grokWeekRemaining ?? existing.grokWeekRemaining
        merged.kimiFiveHourRemaining =
            incoming.kimiFiveHourRemaining ?? existing.kimiFiveHourRemaining
        merged.kimiWeekRemaining =
            incoming.kimiWeekRemaining ?? existing.kimiWeekRemaining
        merged.claudeActivity = mergeActivity(existing.claudeActivity, incoming.claudeActivity)
        merged.codexActivity = mergeActivity(existing.codexActivity, incoming.codexActivity)
        merged.grokActivity = mergeActivity(existing.grokActivity, incoming.grokActivity)
        merged.kimiActivity = mergeActivity(existing.kimiActivity, incoming.kimiActivity)
        return merged
    }

    private func mergeActivity(
        _ existing: [QuotaModelActivity],
        _ incoming: [QuotaModelActivity]
    ) -> [QuotaModelActivity] {
        var totals = Dictionary(uniqueKeysWithValues: existing.map { ($0.model, $0.tokenDelta) })
        for activity in incoming {
            totals[activity.model, default: 0] += activity.tokenDelta
        }
        return totals.map { QuotaModelActivity(model: $0.key, tokenDelta: $0.value) }
            .sorted {
                if $0.tokenDelta == $1.tokenDelta { return $0.model < $1.model }
                return $0.tokenDelta > $1.tokenDelta
            }
    }
}

/// 按当前已用比例外推：周期结束时还剩多少、额度会不会在回满前见底。
struct QuotaPaceForecast: Equatable {
    /// 到回满时刻预计剩余百分比；超支为负数。
    var remainingAtReset: Double
    /// 按现在节奏把剩余额度用完还要几天（不考虑回满）。
    var daysUntilEmpty: Double
    /// 距本周期回满还有几天。
    var daysUntilReset: Double

    var willExhaustBeforeReset: Bool { daysUntilEmpty < daysUntilReset }
}

enum QuotaPace {
    static let minUsedPercent = 3.0
    static let minElapsed: TimeInterval = 3600

    static func forecast(
        usedPercent: Double,
        start: Int,
        end: Int,
        now: Int
    ) -> QuotaPaceForecast? {
        guard usedPercent.isFinite, usedPercent >= minUsedPercent else { return nil }
        let elapsed = Double(now - start)
        let span = Double(end - start)
        guard elapsed >= minElapsed, span > 0, now < end, now > start else { return nil }
        let projectedUsed = usedPercent * span / elapsed
        let remainingAtReset = 100 - projectedUsed
        let daysUntilReset = Double(end - now) / 86_400
        let leftover = max(100 - usedPercent, 0)
        let daysUntilEmpty = leftover == 0
            ? 0
            : leftover / usedPercent * (elapsed / 86_400)
        return QuotaPaceForecast(
            remainingAtReset: remainingAtReset,
            daysUntilEmpty: daysUntilEmpty,
            daysUntilReset: daysUntilReset
        )
    }
}
