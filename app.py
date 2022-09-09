# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 09:08:31 2022

@author: erikb
"""

import pandas as pd #load the pandas library with alias pd
import numpy as np # load numpy for NaN substition
import streamlit as st
from datetime import datetime, timedelta

st.title('GR Timesheet analysis')
st.sidebar.title('Timesheet file upload:')
st.sidebar.write('Please upload the timesheet for analysis')

uploaded_file = st.sidebar.file_uploader("Upload Timesheet File")

#st.sidebar.write('Enter Period Start Date')
#start_date = st.sidebar.text_input("YYYY/MM/DD", key="startdate")

#st.sidebar.write('Enter Period End Date')
#end_date = st.sidebar.text_input("YYYY/MM/DD", key="enddate")


def durationtominutes(x):
    #print(x)
    y = x.split(':')
    hours = y[0]
    minutes = y[1]
    hours = int(hours)
    minutes = int(minutes)
    totalminutes = (hours * 60) + minutes
    return(totalminutes)

def mins_to_hours(x):
    y = x // 60
    y = str(y)
    z = x % 60
    z = str(z)
    z = z.ljust(2, '0')
    z = y + ":" + z
    return(z)


if uploaded_file is not None:

    st.write('Enter Period Start Date')
    start_date = st.text_input("Use Format: YYYY/MM/DD", key="startdate")

    st.write('Enter Period End Date')
    end_date = st.text_input("Use Format: YYYY/MM/DD", key="enddate")
        
    if len(start_date) == 10 and len(end_date) == 10:
        df = pd.read_excel(uploaded_file, sheet_name = 'IndividualTimesheetReport')
        staffname = df.iloc[4,0]
    
        st.subheader("Staff member:")
        st.write(staffname)
        
        # read data from sheet
        df = pd.read_excel(uploaded_file, sheet_name = 'IndividualTimesheetReport', skiprows = 8)
        
        # drop rows where date is NaN
        df = df[df['Date'].notna()]
        # convert data to datetime
        df["Date"] = pd.to_datetime(df["Date"])
        # drop columns with uneeded information
        df = df[['Day','Date','Roster Unit','Cost Centre','CC Override','Name','Shift Times','Work Time (HH:MM)','Normal Hours','Unavailability','ROT (HH:MM)','UOT (HH:MM)','OC','IC','Allowances','Pay Flags','Net Hours Balance']]
        # drop rows where worktime is blank
        df = df[df['Work Time (HH:MM)'].notna()]
        
        ## ADD LINE TO REPLACE ANY 6:00 WITH 7:30 - CHECK IF WANT TO REMOVE
        df = df.replace('6:00','7:30')
        
        # convert hours expressed as 00:00 to minutes, can be reconverted to hourts later.
        df['Normal Hours'] = df['Normal Hours'].apply(durationtominutes)
        df['Work Time (HH:MM)'] = df['Work Time (HH:MM)'].apply(durationtominutes)
        df['Unavailability'] = df['Unavailability'].apply(durationtominutes)
        
        ## COLLECT INPUTS FOR DATE RANGE
        #start_date= "2022/04/01"
        start_date = datetime.strptime(start_date, '%Y/%m/%d')
        start_date= start_date - timedelta(days=1)
        
        #end_date = "2022/07/31"
        end_date = datetime.strptime(end_date, '%Y/%m/%d')
        end_date= end_date + timedelta(days=1)
        
        ## drop data outside of datarange
        mask = (df['Date'] > start_date) & (df['Date'] < end_date)
        df = df.loc[mask]
          
        # PIVOT TO CREATE SUMMARY TABLE ON NAME
        df_summary = pd.pivot_table(df, index=['Name'],values=['Work Time (HH:MM)','Normal Hours','Unavailability'], aggfunc=np.sum)
        df_summary = df_summary.reset_index(drop=False)
        ## Create a set of blanks for when there is no corresponding row - this is to cover the day/ name permu
        # initialize list of lists
        blanks = [['E', 0, 0, 0], ['L', 0, 0, 0], ['LD', 0, 0, 0], ['Ten', 0, 0, 0],['N', 0, 0, 0],['SuE', 0, 0, 0],['SuL', 0, 0, 0],['SuLD', 0, 0, 0],['SuN', 0, 0, 0],['SD-Mand', 0, 0, 0],['SD-NonMand', 0, 0, 0], ['Other PD', 0, 0, 0]]
        df_blank = pd.DataFrame(blanks, columns = ['Name', 'Normal Hours','Unavailability', 'Work Time (HH:MM)'])
        # concatenate dataframe
        # drop rows where name is duplicated keeping first
        df_summary = pd.concat([df_summary,df_blank])
        df_summary = df_summary.drop_duplicates(subset='Name', keep="first")
        df_summary['Total Hours'] = df_summary['Unavailability'] + df_summary['Work Time (HH:MM)']
        df_summary = df_summary.set_index('Name')
        
        # overall total
        norm_total = df_summary["Normal Hours"].sum()
        unav_total = df_summary["Unavailability"].sum()
        work_total = df_summary["Work Time (HH:MM)"].sum()
        overall_tot = work_total + unav_total
        
        #print("Overall Total:")
        #print(overall_tot)
        #x = mins_to_hours(overall_tot)
        # convert minutes to hours and minutes
        
        # contracted
        tot_cont = df_summary.loc['E']['Total Hours'] + df_summary.loc['L']['Total Hours'] + df_summary.loc['LD']['Total Hours'] + df_summary.loc['N']['Total Hours']  + df_summary.loc['Ten']['Total Hours']
        
        # non contracted
        tot_noncont = df_summary.loc['SuE']['Total Hours'] + df_summary.loc['SuL']['Total Hours'] + df_summary.loc['SuLD']['Total Hours'] + df_summary.loc['SuN']['Total Hours']
        
        # sd
        tot_sd = df_summary.loc['SD-Mand']['Total Hours'] + df_summary.loc['SD-NonMand']['Total Hours'] + df_summary.loc['Other PD']['Total Hours']
        
        #total clinical
        tot_clinical = tot_cont + tot_noncont + tot_sd
        
        # total MiL
        tot_MiL = df_summary.loc['MIL']['Total Hours'] + df_summary.loc['MD']['Total Hours']
        
        # total MiL
        tot_AL = df_summary.loc['A/L']['Total Hours'] + df_summary.loc['A/L BH']['Total Hours']
        
        # Total Unaccounted
        unaccounted = overall_tot - (tot_clinical + tot_MiL + tot_AL)
        
        # overall tot
        overall_tot = mins_to_hours(overall_tot)
        st.subheader("Overall Total - " + overall_tot)
        
        #total clinical
        tot_clinical = mins_to_hours(tot_clinical)
        st.write("Clinical Total - " + tot_clinical)
        
        #total MiL
        tot_MiL = mins_to_hours(tot_MiL)
        st.write("MiL Total - " + tot_MiL)
        
        #total AL
        tot_AL = mins_to_hours(tot_AL)
        st.write("A/L Total - " + tot_AL)
        
        # Unaccounted
        unaccounted = mins_to_hours(unaccounted)
        st.write("Unaccounted - " + unaccounted)
    
        # summary table
        st.subheader("Breakdown (Minutes):")
        
        df_summary2 = df[['Day','Date','Name','Work Time (HH:MM)','Unavailability']]
        weekend_days = ['Sat','Sun','sat','sun']
        df_summary2['DoW'] = df_summary2.isin(weekend_days).any(1).astype(int)
        
        df_summary2 = pd.pivot_table(df_summary2, index=['DoW','Name'],values=['Work Time (HH:MM)','Unavailability'], aggfunc=np.sum)
        #df_summary2['Total_Hours'] = df_summary2['Unavailability'] + df_summary2['Work Time (HH:MM)']
        
        df_summary2 = df_summary2.reset_index(drop=False)
        
        df_summary2['DoW'] = df_summary2['DoW'].replace(1,"Sat/Sun")
        df_summary2['DoW'] = df_summary2['DoW'].replace(0,"Mon-Fri")
        
        st.dataframe(df_summary2, width=800)



