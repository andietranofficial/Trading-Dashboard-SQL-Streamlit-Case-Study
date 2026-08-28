-- Below is the final query required to source historical data from the database. 

SELECT 
 
    hist.FactID,
    hist.Date,
    hist.[Open],
    hist.High,
    hist.Low,
    hist.[Close],
    hist.AdjClose,
    hist.Volume,
 
    sec.Company,
    sec.Symbol,
    sec.Industry,
    sec.IndexWeighting,
 
    exc.Symbol AS Exchange
 
FROM [dbo].[FactPrices_Daily] AS hist
 
   INNER JOIN [dbo].[dimSecurity] AS sec 
      ON hist.SecurityID = sec.ID
      
   INNER JOIN [dbo].[dimExchange] AS exc 
      ON sec.ExchangeID = exc.ID


SELECT COUNT(*)
FROM dbo.FactAttributes_Intraday

SELECT COUNT(*)
FROM dbo.FactPrices_Daily
