-- SQL Query to find contracts with the highest value
-- Based on schema.sql structure

WITH ActiveContracts AS (
    SELECT *
    FROM public."HopDong"
    WHERE is_deleted = false OR is_deleted IS NULL
)
SELECT 
    h."ID",
    h."SoHopDong",
    h."GiaTriHopDong",
    h."NgayKy",
    c."TenCongTy",
    g."TenGoiThau"
FROM ActiveContracts h
LEFT JOIN public."CongTy" c ON h."CongTy_ID" = c."ID"
LEFT JOIN public."GoiThau" g ON h."GoiThau_ID" = g."ID"
WHERE h."GiaTriHopDong" = (SELECT MAX("GiaTriHopDong") FROM ActiveContracts);
