import Foundation

// MARK: - Financial Statements

public struct IncomeStatement: Sendable, Codable {
    public let symbol: String; public let fiscalYear: Int; public let period: StatementPeriod
    public let revenue: Double; public let costOfRevenue: Double; public let grossProfit: Double
    public let operatingExpenses: Double; public let operatingIncome: Double
    public let interestExpense: Double; public let incomeBeforeTax: Double
    public let incomeTax: Double; public let netIncome: Double
    public let eps: Double; public let dilutedEPS: Double
    public let ebitda: Double; public let sharesOutstanding: Double

    public init(symbol: String, fiscalYear: Int, period: StatementPeriod, revenue: Double, costOfRevenue: Double, operatingExpenses: Double, operatingIncome: Double, interestExpense: Double = 0, incomeTax: Double = 0, netIncome: Double, eps: Double = 0, dilutedEPS: Double = 0, ebitda: Double = 0, sharesOutstanding: Double = 1) {
        self.symbol = symbol; self.fiscalYear = fiscalYear; self.period = period
        self.revenue = revenue; self.costOfRevenue = costOfRevenue
        self.grossProfit = revenue - costOfRevenue; self.operatingExpenses = operatingExpenses
        self.operatingIncome = operatingIncome; self.interestExpense = interestExpense
        self.incomeBeforeTax = operatingIncome - interestExpense
        self.incomeTax = incomeTax; self.netIncome = netIncome
        self.eps = eps; self.dilutedEPS = dilutedEPS; self.ebitda = ebitda
        self.sharesOutstanding = sharesOutstanding
    }
}

public struct BalanceSheet: Sendable, Codable {
    public let symbol: String; public let fiscalYear: Int; public let period: StatementPeriod
    public let totalAssets: Double; public let totalLiabilities: Double
    public let totalEquity: Double; public let currentAssets: Double
    public let currentLiabilities: Double; public let longTermDebt: Double
    public let cash: Double; public let inventory: Double; public let receivables: Double
    public let payables: Double; public let goodwill: Double; public let bookValuePerShare: Double

    public init(symbol: String, fiscalYear: Int, period: StatementPeriod, totalAssets: Double, totalLiabilities: Double, totalEquity: Double, currentAssets: Double, currentLiabilities: Double, longTermDebt: Double = 0, cash: Double = 0, inventory: Double = 0, receivables: Double = 0, payables: Double = 0, goodwill: Double = 0, bookValuePerShare: Double = 0) {
        self.symbol = symbol; self.fiscalYear = fiscalYear; self.period = period
        self.totalAssets = totalAssets; self.totalLiabilities = totalLiabilities; self.totalEquity = totalEquity
        self.currentAssets = currentAssets; self.currentLiabilities = currentLiabilities
        self.longTermDebt = longTermDebt; self.cash = cash; self.inventory = inventory
        self.receivables = receivables; self.payables = payables; self.goodwill = goodwill
        self.bookValuePerShare = bookValuePerShare
    }
}

public struct CashFlowStatement: Sendable, Codable {
    public let symbol: String; public let fiscalYear: Int; public let period: StatementPeriod
    public let operatingCashFlow: Double; public let capitalExpenditure: Double
    public let freeCashFlow: Double; public let dividends: Double
    public let netBorrowing: Double; public let shareIssuance: Double

    public init(symbol: String, fiscalYear: Int, period: StatementPeriod, operatingCashFlow: Double, capitalExpenditure: Double = 0, freeCashFlow: Double = 0, dividends: Double = 0, netBorrowing: Double = 0, shareIssuance: Double = 0) {
        self.symbol = symbol; self.fiscalYear = fiscalYear; self.period = period
        self.operatingCashFlow = operatingCashFlow; self.capitalExpenditure = capitalExpenditure
        self.freeCashFlow = freeCashFlow; self.dividends = dividends
        self.netBorrowing = netBorrowing; self.shareIssuance = shareIssuance
    }
}

public enum StatementPeriod: String, Sendable, Codable { case annual, quarterly, ttm }

// MARK: - Ratio Reports

public struct RatioReport: Sendable, Codable {
    public let symbol: String; public let fiscalYear: Int
    public let peRatio: Double?; public let forwardPE: Double?; public let pegRatio: Double?
    public let pbRatio: Double?; public let psRatio: Double?; public let evToEBITDA: Double?
    public let dividendYield: Double?; public let marketCap: Double?

    public init(symbol: String, fiscalYear: Int, peRatio: Double? = nil, forwardPE: Double? = nil, pegRatio: Double? = nil, pbRatio: Double? = nil, psRatio: Double? = nil, evToEBITDA: Double? = nil, dividendYield: Double? = nil, marketCap: Double? = nil) {
        self.symbol = symbol; self.fiscalYear = fiscalYear
        self.peRatio = peRatio; self.forwardPE = forwardPE; self.pegRatio = pegRatio
        self.pbRatio = pbRatio; self.psRatio = psRatio; self.evToEBITDA = evToEBITDA
        self.dividendYield = dividendYield; self.marketCap = marketCap
    }
}

public struct ProfitabilityReport: Sendable, Codable {
    public let grossMargin: Double?; public let operatingMargin: Double?; public let netMargin: Double?
    public let ebitdaMargin: Double?; public let roe: Double?; public let roa: Double?; public let roce: Double?
    public init(grossMargin: Double? = nil, operatingMargin: Double? = nil, netMargin: Double? = nil, ebitdaMargin: Double? = nil, roe: Double? = nil, roa: Double? = nil, roce: Double? = nil) {
        self.grossMargin = grossMargin; self.operatingMargin = operatingMargin; self.netMargin = netMargin
        self.ebitdaMargin = ebitdaMargin; self.roe = roe; self.roa = roa; self.roce = roce
    }
}

public struct LiquidityReport: Sendable, Codable {
    public let currentRatio: Double?; public let quickRatio: Double?; public let cashRatio: Double?
    public init(currentRatio: Double? = nil, quickRatio: Double? = nil, cashRatio: Double? = nil) {
        self.currentRatio = currentRatio; self.quickRatio = quickRatio; self.cashRatio = cashRatio
    }
}

public struct LeverageReport: Sendable, Codable {
    public let debtToEquity: Double?; public let debtRatio: Double?; public let interestCoverage: Double?
    public init(debtToEquity: Double? = nil, debtRatio: Double? = nil, interestCoverage: Double? = nil) {
        self.debtToEquity = debtToEquity; self.debtRatio = debtRatio; self.interestCoverage = interestCoverage
    }
}

public struct EfficiencyReport: Sendable, Codable {
    public let assetTurnover: Double?; public let inventoryTurnover: Double?
    public init(assetTurnover: Double? = nil, inventoryTurnover: Double? = nil) {
        self.assetTurnover = assetTurnover; self.inventoryTurnover = inventoryTurnover
    }
}

public struct GrowthReport: Sendable, Codable {
    public let revenueGrowth: Double?; public let epsGrowth: Double?; public let netIncomeGrowth: Double?
    public let fcfGrowth: Double?; public let revenueCAGR: Double?; public let epsCAGR: Double?
    public init(revenueGrowth: Double? = nil, epsGrowth: Double? = nil, netIncomeGrowth: Double? = nil, fcfGrowth: Double? = nil, revenueCAGR: Double? = nil, epsCAGR: Double? = nil) {
        self.revenueGrowth = revenueGrowth; self.epsGrowth = epsGrowth; self.netIncomeGrowth = netIncomeGrowth
        self.fcfGrowth = fcfGrowth; self.revenueCAGR = revenueCAGR; self.epsCAGR = epsCAGR
    }
}

public struct ValuationResult: Sendable, Codable {
    public let dcfValue: Double?; public let grahamValue: Double?; public let epvValue: Double?
    public let averageValue: Double?; public let marginOfSafety: Double?
    public init(dcfValue: Double? = nil, grahamValue: Double? = nil, epvValue: Double? = nil, averageValue: Double? = nil, marginOfSafety: Double? = nil) {
        self.dcfValue = dcfValue; self.grahamValue = grahamValue; self.epvValue = epvValue
        self.averageValue = averageValue; self.marginOfSafety = marginOfSafety
    }
}

public struct FundamentalScore: Sendable, Codable {
    public let total: Double
    public let rating: Rating
    public let components: [String: Double]

    public enum Rating: String, Sendable, Codable {
        case excellent, strong, good, average, weak
    }

    public init(total: Double, components: [String: Double]) {
        self.total = min(100, max(0, total)); self.components = components
        switch self.total {
        case 85...100: rating = .excellent; case 70..<85: rating = .strong
        case 55..<70: rating = .good; case 40..<55: rating = .average
        default: rating = .weak
        }
    }
}
