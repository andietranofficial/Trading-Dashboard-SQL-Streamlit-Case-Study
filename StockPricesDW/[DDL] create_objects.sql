----- PART 1: Create schema and tables -----

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'dbo'
)
BEGIN
    EXEC('CREATE SCHEMA dbo');
END;
GO

-- Drop in dependency order (facts before dimensions, dimSecurity before dimExchange)
IF OBJECT_ID('dbo.FactAttributes_Intraday', 'U') IS NOT NULL DROP TABLE dbo.FactAttributes_Intraday;
IF OBJECT_ID('dbo.FactPrices_Daily', 'U') IS NOT NULL DROP TABLE dbo.FactPrices_Daily;
IF OBJECT_ID('dbo.dimSecurity', 'U') IS NOT NULL DROP TABLE dbo.dimSecurity;
IF OBJECT_ID('dbo.dimExchange', 'U') IS NOT NULL DROP TABLE dbo.dimExchange;
GO

CREATE TABLE dbo.dimExchange (
    ID       INT           NOT NULL,
    Symbol   VARCHAR(20)   NOT NULL,
    Type     VARCHAR(50)   NOT NULL,
    Location VARCHAR(50)   NOT NULL,
    Currency VARCHAR(20)   NOT NULL,
    Website  VARCHAR(100)  NOT NULL,

    CONSTRAINT PK_dimExchange PRIMARY KEY CLUSTERED (ID)
);
GO

CREATE TABLE dbo.dimSecurity (
    ID              INT             NOT NULL,
    Symbol          VARCHAR(10)     NOT NULL,
    Company         VARCHAR(100)    NOT NULL,
    Industry        VARCHAR(100)    NOT NULL,
    DateAdded       DATE            NOT NULL,
    IndexWeighting  DECIMAL(9,6)    NOT NULL,
    ExchangeID      INT             NOT NULL,

    CONSTRAINT PK_dimSecurity PRIMARY KEY CLUSTERED (ID),
    CONSTRAINT FK_dimSecurity_dimExchange FOREIGN KEY (ExchangeID) REFERENCES dbo.dimExchange (ID)
);
GO

CREATE TABLE dbo.FactPrices_Daily (
    FactID      INT             NOT NULL,
    [Date]      DATE            NOT NULL,
    [Open]      DECIMAL(10,5)   NOT NULL,
    High        DECIMAL(10,5)   NOT NULL,
    Low         DECIMAL(10,5)   NOT NULL,
    [Close]     DECIMAL(10,5)   NOT NULL,
    AdjClose    DECIMAL(10,5)   NOT NULL,
    Volume      BIGINT          NOT NULL,
    SecurityID  INT             NOT NULL,

    CONSTRAINT PK_FactPrices_Daily PRIMARY KEY CLUSTERED (FactID),
    CONSTRAINT FK_FactPrices_Daily_dimSecurity FOREIGN KEY (SecurityID) REFERENCES dbo.dimSecurity (ID)
);
GO

CREATE TABLE dbo.FactAttributes_Intraday (
    FactID      INT             NOT NULL,
    [DateTime]  DATETIME2(7)    NOT NULL,
    LastBid     DECIMAL(10,5)   NOT NULL,
    High        DECIMAL(10,5)   NOT NULL,
    Low         DECIMAL(10,5)   NOT NULL,
    [Open]      DECIMAL(10,5)   NOT NULL,
    Volume      BIGINT          NOT NULL,
    MarketCap   BIGINT          NOT NULL,
    Beta        DECIMAL(5,3)    NOT NULL,
    SecurityID  INT             NOT NULL,

    CONSTRAINT PK_FactAttributes_Intraday PRIMARY KEY CLUSTERED (FactID),
    CONSTRAINT FK_FactAttributes_Intraday_dimSecurity FOREIGN KEY (SecurityID) REFERENCES dbo.dimSecurity (ID)
);
GO
