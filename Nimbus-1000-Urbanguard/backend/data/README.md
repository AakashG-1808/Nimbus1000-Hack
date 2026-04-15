# BBMP Grievances Data

Place BBMP CSV files here. Download from:
https://data.opencity.in/dataset/bbmp-grievances-data

Expected filename pattern: `bbmp_grievances_*.csv` or `bbmp_*.csv`

## CSV Column Mapping

The loader handles these common BBMP column names:
- Ward: `ward_name`, `Ward Name`, `ward`
- Category: `grievance_type`, `Grievance Type`, `category`, `Category`
- Description: `description`, `Description`, `complaint_details`
- Date: `created_date`, `Created Date`, `date`, `Date`, `complaint_date`

## Usage

Once you place the CSV file(s) here, restart the backend.
The loader will automatically use real data instead of simulated data.
