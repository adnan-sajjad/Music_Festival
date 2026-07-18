/*====================================================================
MUSIC FESTIVAL DATA ANALYSIS PROJECT
====================================

Project Title : Music Festival Revenue & Artist Performance Analysis
Tools Used    : MySQL, Power BI
Author        : Adnan Sajjad Makrani

Project Objectives:

1. Clean and standardize raw festival and artist datasets.
2. Handle missing values and duplicate records.
3. Perform exploratory data analysis (EDA).
4. Generate festival, artist, and revenue insights.
5. Apply advanced SQL techniques such as:

   * CTEs
   * Window Functions
   * Ranking Functions
   * Revenue Contribution Analysis
   * Month-over-Month Growth Analysis
6. Prepare data for Power BI dashboard development.

====================================================================*/

/*====================================================================
STEP 1 : DATA PREPARATION
====================================================================*/

/*
Create a working copy of the raw dataset.
This preserves the original source table for future reference.
*/

CREATE TABLE music_festival AS
SELECT *
FROM music_festival_raw;

/*====================================================================
STEP 2 : DATE STANDARDIZATION
====================================================================*/

/*
Identify different date formats and convert them into
a standard SQL DATE format.
*/

SELECT
date,
CASE
WHEN date LIKE '%/%'
THEN STR_TO_DATE(date,'%d/%m/%Y')
WHEN date LIKE '%-%'
THEN STR_TO_DATE(date,'%d-%m-%Y')
END AS standard_date
FROM music_festival;

/*
Create a new DATE column to store cleaned dates.
*/

ALTER TABLE music_festival
ADD COLUMN date_clean DATE AFTER date;

/*
Populate standardized date values.
*/

UPDATE music_festival
SET date_clean =
CASE
WHEN date LIKE '%/%'
THEN STR_TO_DATE(date,'%d/%m/%Y')
WHEN date LIKE '%-%'
THEN STR_TO_DATE(date,'%d-%m-%Y')
END;

/*
Replace original date column with cleaned date column.
*/

ALTER TABLE music_festival
DROP COLUMN date;

ALTER TABLE music_festival
RENAME COLUMN date_clean TO date;

/*====================================================================
STEP 3 : COLUMN STANDARDIZATION
====================================================================*/

/*
Rename columns using SQL naming conventions:

* lowercase
* snake_case
* no spaces or special characters
  */

/*====================================================================
STEP 4 : MISSING VALUE ANALYSIS
====================================================================*/

/*
Check missing values in Tour Name.
*/

SELECT
COUNT(*) AS total_rows,
SUM(CASE WHEN tour_name IS NULL THEN 1 ELSE 0 END) AS null_count,
SUM(CASE WHEN tour_name='' THEN 1 ELSE 0 END) AS empty_count
FROM music_festival;

/*
Replace missing tour names with a default category.
*/

UPDATE music_festival
SET tour_name='Unknown Tour'
WHERE tour_name='';

/*
Convert blank Ticket Price values to NULL.
*/

UPDATE music_festival
SET ticket_price=NULL
WHERE TRIM(ticket_price)='';

/*
Convert blank Attendance values to NULL.
*/

UPDATE music_festival
SET total_attendance=NULL
WHERE TRIM(total_attendance)='';

/*
Impute missing Ticket Price values using
the overall average ticket price.
*/

UPDATE music_festival
SET ticket_price=
(
SELECT avg_price
FROM(
SELECT ROUND(AVG(ticket_price),2) avg_price
FROM music_festival
WHERE ticket_price IS NOT NULL
)t
)
WHERE ticket_price IS NULL;

/*
Impute missing Attendance values using
average festival attendance.
*/

UPDATE music_festival
SET total_attendance=
(
SELECT avg_attendance
FROM(
SELECT ROUND(AVG(total_attendance))
AS avg_attendance
FROM music_festival
WHERE total_attendance IS NOT NULL
)t
)
WHERE total_attendance IS NULL;

/*====================================================================
STEP 5 : DATA TYPE CONVERSION
====================================================================*/

/*
Convert numeric columns into appropriate data types
for efficient analysis.
*/

ALTER TABLE music_festival
MODIFY ticket_price DECIMAL(10,2),
MODIFY total_attendance INT,
MODIFY merchandise_sales BIGINT,
MODIFY sponsorship_revenue BIGINT,
MODIFY total_revenue BIGINT;

/*====================================================================
STEP 6 : DUPLICATE DETECTION
====================================================================*/

/*
Identify duplicate festival records based on:
Festival Name, City, Event Date and Headlining Artist.
*/

WITH duplicate_check AS(
SELECT *,
ROW_NUMBER() OVER(
PARTITION BY festival_name,
city,
date,
headlining_artist
ORDER BY festival_name
) rn
FROM music_festival
)
SELECT *
FROM duplicate_check
WHERE rn>1;

/*
Remove duplicate records while preserving
the first occurrence.
*/

/*====================================================================
STEP 7 : ARTIST DATASET STANDARDIZATION
====================================================================*/

/*
Rename artist table and standardize column names.
*/

ALTER TABLE artist_popularity_data
RENAME TO artist_popularity;

/*
Populate missing attendance value for Bryan Adams
using festival attendance averages.
*/

UPDATE artist_popularity ap
JOIN(
SELECT
ROUND(AVG(total_attendance),0) avg_attendance
FROM music_festival
WHERE headlining_artist='Bryan Adams'
) mf
SET ap.average_attendance_per_city=mf.avg_attendance
WHERE ap.artist_name='Bryan Adams';

/*
Remove unnecessary spaces from categorical fields.
*/

UPDATE artist_popularity
SET tour_impact=TRIM(tour_impact);

/*====================================================================
EXPLORATORY DATA ANALYSIS (EDA)
====================================================================*/

/* Q1 : Calculate Total Revenue Generated */

SELECT
SUM(total_revenue) AS total_revenue
FROM music_festival;

/* Q2 : Calculate Total Festival Attendance */

SELECT
SUM(total_attendance) AS total_attendance
FROM music_festival;

/* Q3 : Calculate Average Ticket Price */

SELECT
ROUND(AVG(ticket_price),2) AS avg_ticket_price
FROM music_festival;

/* Q4 : Count Unique Festivals */

SELECT
COUNT(DISTINCT festival_name) AS no_of_festival
FROM music_festival;

/*====================================================================
BUSINESS ANALYSIS
====================================================================*/

/* Q5 : Top 10 Revenue Generating Festivals */

SELECT
festival_name,
SUM(total_revenue) AS total_revenue
FROM music_festival
GROUP BY festival_name
ORDER BY total_revenue DESC
LIMIT 10;

/* Q6 : Revenue Performance by City */

SELECT
city,
SUM(total_revenue) AS total_revenue
FROM music_festival
GROUP BY city
ORDER BY total_revenue DESC;

/* Q7 : Top Artists by Revenue Generated */

SELECT
headlining_artist,
SUM(total_revenue) AS total_revenue
FROM music_festival
GROUP BY headlining_artist
ORDER BY total_revenue DESC;

/* Q8 : Top Artists by Audience Attendance */

SELECT
headlining_artist,
SUM(total_attendance) AS attendance
FROM music_festival
GROUP BY headlining_artist
ORDER BY attendance DESC;

/* Q9 : Artists with Highest Average Ticket Price */

SELECT
headlining_artist,
ROUND(AVG(ticket_price),2) AS avg_ticket_price
FROM music_festival
GROUP BY headlining_artist
ORDER BY avg_ticket_price DESC;

/*====================================================================
ADVANCED SQL ANALYSIS
====================================================================*/

/* Q10 : Rank Festivals by Revenue */

SELECT
festival_name,
SUM(total_revenue) AS total_revenue,
DENSE_RANK() OVER(
ORDER BY SUM(total_revenue) DESC
) AS festival_rank
FROM music_festival
GROUP BY festival_name;

/* Q11 : Revenue Contribution Percentage */

WITH revenue_cte AS(
SELECT
festival_name,
SUM(total_revenue) AS revenue
FROM music_festival
GROUP BY festival_name
)
SELECT
festival_name,
revenue,
ROUND(
revenue*100.0/
SUM(revenue) OVER(),2
) AS contribution_pct
FROM revenue_cte
ORDER BY contribution_pct DESC;

/* Q12 : Monthly Revenue Trend */

SELECT
DATE_FORMAT(date,'%Y-%m') AS month,
SUM(total_revenue) AS revenue
FROM music_festival
GROUP BY month
ORDER BY month;

/* Q13 : Month-over-Month Revenue Growth */

WITH monthly_revenue AS(
SELECT
DATE_FORMAT(date,'%Y-%m') AS month,
SUM(total_revenue) AS revenue
FROM music_festival
GROUP BY month
)
SELECT
month,
revenue,
LAG(revenue) OVER(ORDER BY month) AS prev_month,
ROUND(
(revenue-LAG(revenue) OVER(ORDER BY month))
*100.0/
LAG(revenue) OVER(ORDER BY month),
2
) AS growth_pct
FROM monthly_revenue;

/* Q14 : Top Revenue Festival in Each City */

WITH city_rank AS(
SELECT
city,
festival_name,
SUM(total_revenue) AS revenue,
ROW_NUMBER() OVER(
PARTITION BY city
ORDER BY SUM(total_revenue) DESC
) AS rn
FROM music_festival
GROUP BY city,festival_name
)
SELECT *
FROM city_rank
WHERE rn=1;

/*====================================================================
ARTIST PERFORMANCE ANALYSIS
====================================================================*/

/* Top Artists by Streaming Popularity */

SELECT
artist_name,
genre,
streaming_plays_in_M
FROM artist_popularity
ORDER BY streaming_plays_in_M DESC;

/* Compare Social Media Followers vs Streaming Plays */

SELECT
artist_name,
followers_in_M,
streaming_plays_in_M
FROM artist_popularity;

/* Analyze Genre Popularity */

SELECT
genre,
COUNT(*) AS genre_count
FROM artist_popularity
GROUP BY genre
ORDER BY genre_count DESC;

/*====================================================================
END OF PROJECT
====================================================================*/
