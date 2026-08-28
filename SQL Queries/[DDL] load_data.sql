----- PART 2: Load data -----
-- BULK INSERT runs on the SQL Server host's file system, not the client's.
-- Requires SQLCMD mode (SSMS: Query > SQLCMD Mode, or run via the sqlcmd utility).
-- DataPath comes from local.settings.sql (gitignored, machine-specific) —
-- copy local.settings.example.sql to create it if it doesn't exist yet.

:r ".\local.settings.sql"

DECLARE @DataPath VARCHAR(260) = '$(DataPath)';
DECLARE @SQL NVARCHAR(MAX);

-- Load order: dimExchange, dimSecurity before the fact tables that reference them.

SET @SQL = '
BULK INSERT dbo.dimExchange
FROM ''' + @DataPath + 'dimExchange.csv''
WITH (
    FORMAT = ''CSV'',
    FIRSTROW = 2,
    FIELDTERMINATOR = '','',
    ROWTERMINATOR = ''0x0a'',
    CODEPAGE = ''65001'',
    TABLOCK
);';
EXEC sp_executesql @SQL;

SET @SQL = '
BULK INSERT dbo.dimSecurity
FROM ''' + @DataPath + 'dimSecurity.csv''
WITH (
    FORMAT = ''CSV'',
    FIRSTROW = 2,
    FIELDTERMINATOR = '','',
    ROWTERMINATOR = ''0x0a'',
    CODEPAGE = ''65001'',
    TABLOCK
);';
EXEC sp_executesql @SQL;

SET @SQL = '
BULK INSERT dbo.FactPrices_Daily
FROM ''' + @DataPath + 'FactPrices_Daily.csv''
WITH (
    FORMAT = ''CSV'',
    FIRSTROW = 2,
    FIELDTERMINATOR = '','',
    ROWTERMINATOR = ''0x0a'',
    CODEPAGE = ''65001'',
    TABLOCK
);';
EXEC sp_executesql @SQL;

SET @SQL = '
BULK INSERT dbo.FactAttributes_Intraday
FROM ''' + @DataPath + 'FactAttributes_Intraday.csv''
WITH (
    FORMAT = ''CSV'',
    FIRSTROW = 2,
    FIELDTERMINATOR = '','',
    ROWTERMINATOR = ''0x0a'',
    CODEPAGE = ''65001'',
    TABLOCK
);';
EXEC sp_executesql @SQL;
GO

SELECT COUNT(*) AS dimExchange_Rows FROM dbo.dimExchange;
SELECT COUNT(*) AS dimSecurity_Rows FROM dbo.dimSecurity;
SELECT COUNT(*) AS FactPrices_Daily_Rows FROM dbo.FactPrices_Daily;
SELECT COUNT(*) AS FactAttributes_Intraday_Rows FROM dbo.FactAttributes_Intraday;
