import streamlit as st 
import pandas as pd 
import plotly.express as px 
from fpdf import FPDF 
import numpy as np 


class PDFReport(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, "Datatally Business analysis report", ln=1, align="C")

    def footer(self):
        pass



st.markdown(
    """
    <style>
    .stApp {
        background-color: #F3EEE4;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        padding-top: 1rem;
    }
    h1 {
        color: #1F3A5F;
    }
    h2, h3 {
        color: #2B4C7E;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_column_name(column):
  return column.strip().lower().replace("_", "").replace(" ", "")


def find_columns(df, possible_columns):
    mapping = {}

    normalized_columns = [
        normalize_column_name(column)
        for column in df.columns
    ]


    if len(normalized_columns) != len(set(normalized_columns)):
        st.error("Duplicate or ambiguous column names detected.")
        st.stop()

    normalized_df_columns = {
        normalize_column_name(column): column
        for column in df.columns}

    
    
    for standard_name, possible_names in possible_columns.items():
        

        exact_name = normalize_column_name(standard_name)
        if exact_name in normalized_df_columns:
           mapping[normalized_df_columns[exact_name]] = standard_name
           continue
        
        matched_columns =[]

        for possible_name in possible_names:
            normalized_name = normalize_column_name(possible_name)
            if normalized_name in normalized_df_columns:
                original_column = normalized_df_columns[normalized_name]
                matched_columns.append(original_column)

        if len(matched_columns)>1:
           st.error(
               f"Multiple columns detected for {standard_name}: "
               f"{matched_columns}. Please keep only one.")
           st.stop() 

        elif len(matched_columns) == 1:
             mapping[matched_columns[0]] = standard_name     

                
               
    return mapping





st.set_page_config(
    page_title = 'DataTally',
    layout= 'wide'

)

col1,col2 = st.columns([1,5])
with col1:
    st.image("data/app logo.png",width =200)
with col2:
    st.title("DataTally")  
    st.write("Turn your raw sales data into clear business insights.") 

st.divider()  

st.subheader("What DataTally can do")

col1, col2, col3, col4= st.columns(4)

with col1:
    st.markdown("# :material/bar_chart:")
    st.markdown("**Analyze Sales**")

with col2:
   st.markdown("# :material/lightbulb:")
   st.markdown("**Business Insights**")

with col3:
   st.markdown("# :material/pie_chart:")
   st.markdown("**Visualize Revenue**") 




st.header("Upload your dataset")

possible_columns = {
    'Date': ['Date', 'InvoiceDate', 'OrderDate', 'SalesDate', 'TransactionDate'],
    'Product': ['Product', 'ProductName', 'Item', 'ItemName', 'Description'],
    'Quantity': ['Quantity', 'Qty', 'Units', 'UnitsSold'],
    'Revenue': ['Revenue', 'Sales', 'SalesAmount', 'TotalSales', 'Amount'],
    'Cost': ['Cost', 'TotalCost', 'COGS', 'CostOfGoodsSold', 'PurchaseCost'],
    'UnitCost': ['UnitCost', 'CostPrice', 'PurchasePrice', 'PricePerUnit'],
    'Customer': ['Customer', 'CustomerID', 'ClientID', 'Client'],
    'Country': ['Country', 'Region', 'Location']
}


uploaded_file =st.file_uploader("Upload your sales data",type =['csv','xlsx','xls'])
with st.spinner("Processing your data..."):


 if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
           df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx','.xls')):
           df = pd.read_excel(uploaded_file)
                
        st.success("File uploaded sucessfully")
        #st.dataframe(df.head()) 

        #detect columns 
        mapping = find_columns(df,possible_columns)
        missing_columns = []
        for standard_name in possible_columns:
           if standard_name not in mapping.values():
              missing_columns.append(standard_name)

        required_columns =["Date","Product","Revenue",]   
        missing_required = []

        for column in required_columns:
           if column in missing_columns:
              missing_required.append(column)
        for column in missing_required:
           selected_column = st.selectbox(
               f"Which column represents {column}?",
               df.columns)
           mapping[selected_column] = column
           


        #st.write("Detected columns:",mapping) 

        df_renamed = df.rename(columns = mapping)
        #print(df_renamed)
        #st.write('Renamed columns:',df_renamed.columns.tolist())
        #st.dataframe(df_renamed)
        #st.write(df.columns)

        required_columns =['Date','Product','Revenue']
       
        missing_columns =[]
        for column in required_columns:
             if column not in df_renamed.columns:
               missing_columns.append(column)
        if missing_columns:
             st.error(f"Missing required columns: {missing_columns}")
             st.stop()

        df_renamed["Date"] = pd.to_datetime(df_renamed["Date"],errors = "coerce")
        df_renamed['Revenue']= pd.to_numeric(df_renamed['Revenue'],errors = "coerce")  
        df_renamed = df_renamed.dropna(subset=["Date", "Revenue"])  
        if df_renamed.empty:
          st.error("No valid data found. Please upload a dataset with valid Date and Revenue values.")
          st.stop() 


        total_revenue = df_renamed["Revenue"].sum()
        total_order = len(df_renamed)


        product_revenue = df_renamed.groupby('Product')["Revenue"].sum().sort_values(ascending =False)

        product_monthly_revenue = (df_renamed.groupby([pd.Grouper(key = "Date",freq ="ME"),"Product"])["Revenue"].sum())

        top_product_each_month = product_monthly_revenue.groupby(level ="Date").idxmax()
        #st.write(product_monthly_revenue)

        if 'Quantity' in df_renamed.columns:
           df_renamed['Quantity'] = pd.to_numeric(df_renamed['Quantity'],errors ="coerce")
           product_quantity = df_renamed.groupby("Product")["Quantity"].sum().sort_values(ascending=False)
        #else:
            #st.write("Quantity data is not available in this dataset.")

        profit_available = False    
        if 'Cost' in  df_renamed.columns:
           df_renamed['Cost']= pd.to_numeric(df_renamed["Cost"],errors ='coerce')  
           profit_available = True

        elif 'UnitCost' in df_renamed.columns and 'Quantity' in df_renamed.columns: 
            df_renamed['UnitCost'] = pd.to_numeric(
            df_renamed['UnitCost'],
            errors='coerce' ) 

            df_renamed['Cost'] = (df_renamed['UnitCost']*df_renamed['Quantity'])
            profit_available = True 

        elif 'UnitCost' in df_renamed.columns:
          st.warning(
            "UnitCost is available, but Quantity is missing. "
            "Total cost cannot be calculated.")

        #else:
            #st.write(
              #"Cost information is not available. "
              #"Profit analysis cannot be calculated.")
            
        if profit_available:    
           df_renamed['Profit'] = df_renamed['Revenue'] - df_renamed['Cost']
           total_profit = df_renamed['Profit'].sum()

           product_profit = df_renamed.groupby('Product')['Profit'].sum().sort_values(ascending=False)
           loss_products = (product_profit < 0).sum()

           df_renamed['profit_margin']= np.where(df_renamed['Revenue']!=0, 
                                                 
           (df_renamed['Profit'] / df_renamed['Revenue']) * 100,
           np.nan)

           profit_margin = np.where(
           total_revenue != 0,
           (total_profit / total_revenue) * 100,
            np.nan)


        top_product =product_revenue.index[0] 
        top_product_revenue =product_revenue.iloc[0]

        top_product = product_revenue.idxmax()
        top_product_revenue = product_revenue.max()

        if "Customer" in df_renamed.columns:
          customer_revenue = df_renamed.groupby('Customer')['Revenue'].sum().sort_values(ascending=False)
          total_customer = df_renamed["Customer"].nunique()
          top_customer = customer_revenue.index[0]
          top_customer_revenue =customer_revenue.iloc[0]
        #else:
          #st.write("Customer data is not available in this dataset.")  

        if "Country" in df_renamed.columns:
         country_revenue = df_renamed.groupby('Country')['Revenue'].sum().sort_values(ascending=False)
         total_country = df_renamed["Country"].nunique()
         top_country = country_revenue.index[0]
         top_country_revenue = country_revenue.iloc[0]
        #else: 
           # st.write("Country data is not available in this dataset.")  
         

        monthly_revenue = df_renamed.set_index("Date")["Revenue"].resample("ME").sum()

        if len(monthly_revenue)>=2:
           latest_revenue = monthly_revenue.iloc[-1]
           
           previous_revenue =monthly_revenue.iloc[-2]
           if previous_revenue!=0:
             revenue_change = (latest_revenue-previous_revenue)/previous_revenue *100
           else:
             revenue_change =None  
        else:
           revenue_change = None 




      

        option = st.segmented_control(
        "What would you like to see?",
        ["Visualize", "Business Insights", "Data Summary",])


        if option == "Visualize":
             #st.subheader("Visualization section")
            visual_type = st.selectbox(
                "Choose visualization",
               ["Revenue", "Products", "Customers", "Countries","Profit and Loss"]


             )
            st.write("Selected:", visual_type)
              
            if visual_type =='Revenue':
               st.subheader("Revenue Visualization")

 
               st.subheader("Revenue Over Time")

                #st.line_chart(monthly_revenue)
               revenue = monthly_revenue.reset_index()
               revenue.columns = ['Month','Revenue']

               fig = px.area(revenue,x ="Month",y = "Revenue",labels ={"Month":"Month","Revenue":"Revenue"},markers =True)
               fig.update_traces(line_color="green",line_width =3)

               st.plotly_chart(fig, use_container_width=True,height =300)
                

            elif visual_type ==  "Products" :
               st.subheader("Product Visualization")
               col1,col2 = st.columns(2)

               with col1:
                  st.subheader("Top Products by Revenue")
                  top_products_revenue = product_revenue.head(10).reset_index(name="Revenue")

                  fig = px.bar(top_products_revenue,x ="Product",y = "Revenue",labels ={"Product":"Product","Revenue":"Revenue"})
                  fig.update_traces(marker_color="purple")

                  st.plotly_chart(fig, use_container_width=True,height =400)
                                                                                            
               with col2:
                   if "Quantity" in df_renamed.columns:
                      
                      st.subheader("Top Product by Quantity")
                      top_products_quantity = product_quantity.head(10).reset_index(name="Quantity")

                      fig = px.bar(top_products_quantity,x ="Product",y = "Quantity",labels ={"Product":"Product","Quantity":"Quantity"})
                      fig.update_traces(marker_color="orange")

                      st.plotly_chart(fig, use_container_width=True,height =400)
                   else:
                      st.write("Quantity data is not available in this dataset.")   


            elif visual_type == "Customers" : 
               if "Customer" in df_renamed.columns:  
                 st.subheader("Top Customers by Revenue") 
                 top_customer =customer_revenue.head(10).reset_index(name = "Revenue") 

                 fig = px.area(top_customer,x ="Customer",y ="Revenue",labels ={"Customer":"Customer ","Revenue":"Revenue"})
                 fig.update_traces(line_color="green")
               
                 st.plotly_chart(fig,  use_container_width=True,height =300)
               else:
                 st.write("Customer data is not available in this dataset.") 

            elif visual_type =="Countries":
               if 'Country' in df_renamed.columns:
                 st.subheader("Top Country by Revenue")
                 top_country = country_revenue.head(10).reset_index(name ="Revenue")

                 fig = px.area(top_country,x ="Country",y ="Revenue",labels ={"Country":"Country ","Revenue":"Revenue"})
                 fig.update_traces(line_color="green")

                 st.plotly_chart(fig,  use_container_width=True,height =250)
               else:  
                   st.write("Country data is not available in this dataset.")  

            elif visual_type =="Profit and Loss":
               if profit_available:
                  st.subheader("Profit & Loss by Product")
                  fig = px.area(
                       product_profit,
                       x=product_profit.index,
                       y=product_profit.values,
                       labels={
                           "x": "Product",
                           "y": "Profit"
                         },
                         title="Profit by Product"
                  )  
                  st.plotly_chart(fig, use_container_width=True) 
               else:
                  st.write("Cost data isnot available")     
                           


        elif option == "Business Insights": 

                
            st.subheader("Business Insights")

            with st.container(border=True):
              st.markdown(
              f":material/trophy: **Top Product:** {top_product} generated"
              f"{top_product_revenue:,.2f} in revenue.")

            if profit_available:  

             with st.container(border=True):
              st.markdown(
              f":material/paid: **Total Profit:** "
              f"{total_profit:,.2f} earned after covering product costs.")

             with st.container(border=True):
              st.markdown(
              f":material/percent: **Profit Margin:** "
              f"{profit_margin:.2f}% of total revenue remained as profit.")

             with st.container(border=True):
              st.markdown(
              f":material/warning: **Loss-Making Products:** "
              f"{loss_products} product(s) generated a loss.")
    
    
    

            if "Customer" in df_renamed.columns:  
               with st.container(border=True):
                st.markdown(
                f":material/person: **Top Customer:** {top_customer} generated "
                f"{top_customer_revenue:,.2f} in revenue.")
            #else:
              # st.write("Customer data is not available in this dataset.")   

              

            if "Country" in df_renamed.columns:

               with st.container(border=True):
                 st.write(
                 f":material/public: **Top Country:** {top_country} generated"
                 f"{top_country_revenue:,.2f} in revenue.")
            #else:
              #st.write("Country data is not available in this dataset.")    
    

            with st.container(border=True):

             if revenue_change == None:
               st.markdown(":material/insert_chart:**Revenue Trend:** Not enough data to compare"
               "revenue with the previous month.")
             
             elif revenue_change > 0:
              st.write(
              f":material/trending_up:**Revenue Trend:** Revenue increased by"
              f"{revenue_change:.2f}% compared with the previous month.")
        
             elif revenue_change < 0:
              st.write(
              f":material/trending_down:**Revenue Trend:** Revenue decreased by"
              f"{abs(revenue_change):.2f}% compared with the previous month.")
        
             else:
              st.write(
             ":material/trending_flat: **Revenue Trend:** Revenue remained unchanged "
            "compared with the previous month.")
         

            average_revenue = monthly_revenue.mean()
            std_revenue = monthly_revenue.std()
        
            upper_limit = average_revenue + 2 * std_revenue
            lower_limit = average_revenue - 2 * std_revenue

            best_month = monthly_revenue.idxmax()
            best_month_revenue = monthly_revenue.max()
        
            unusual_months = monthly_revenue[
            (monthly_revenue > upper_limit) |
            (monthly_revenue < lower_limit)
                
                ]

            with st.container(border=True):
             if len(unusual_months) > 0:
               st.write(
               f":material/warning: **Revenue Anomaly:** "
               f"{len(unusual_months)} unusual revenue month(s) detected.")
        
             else:
              st.write(
              ":material/check_circle: **Revenue Anomaly:** No unusual revenue months detected.")
        

            with st.container(border=True):
             st.write(
             f":material/calendar_month: **Best Month:** {best_month.strftime('%B %Y')} "
             f"with revenue of {best_month_revenue:,.2f}.")
    

            st.subheader("Business Recommendations")

            if revenue_change ==None:
               st.info( "**Revenue Trend:** There is not enough data to compare "
               "revenue with the previous month.")
               

            elif revenue_change>0:
               st.success( f"**Growth Opportunity:** Revenue increased by "
               f"{revenue_change:.2f}% compared with the previous month. "
               f"Continue monitoring the products and markets contributing to this growth.") 

            elif revenue_change<0:   
              st.warning( f"**Attention Needed:** Revenue decreased by "
              f"{abs(revenue_change):.2f}% compared with the previous month. "
              f"Review recent product and customer performance to identify possible causes.")

            else:
              st.info (
              "**Stable Performance:** Revenue remained unchanged compared with "
              "the previous month. Continue monitoring sales performance.")

            average_monthly_revenue = monthly_revenue.mean()
            highest_revenue_month = monthly_revenue.max()  

            st.subheader("Revenue Summary")
            
            st.metric("Total Revenue", total_revenue)

            st.write(
              f"Your business generated a total revenue of "
              f"{total_revenue:,.2f} during the selected period.")

            col1,col2= st.columns(2)
            
            with col1:
             st.metric("Average Monthly Revenue", f"{average_monthly_revenue:,.2f}")

             st.write(
             f"On average,your business generated"
             f"{average_monthly_revenue:,.2f} in revenue per month."
              )
            
            
            with col2:
             st.metric("Highest Monthly Revenue", f"{highest_revenue_month:,.2f}")  
             st.write(
                 f"Your highest monthly revenue was "
                 f"{highest_revenue_month:,.2f}.")
             #st.write(average_monthly_revenue)
             #st.write(type(average_monthly_revenue))  

            if st.button("Generate PDF Report"):

              pdf = PDFReport()
              pdf.add_page()

              pdf.set_font("Helvetica", "B", 16)
              pdf.cell(0, 10, "Revenue Summary", ln=1)

              pdf.set_font("Helvetica","",11)
              pdf.multi_cell(0,8, f"Total Revenue: {total_revenue:,.2f}")
              pdf.set_x(10)
              pdf.multi_cell(0,8,f"Average Monthly Revenue: {average_monthly_revenue:,.2f}")
              pdf.set_x(10)
              pdf.multi_cell(0,8,f"Highest_monthly_revenue, {highest_revenue_month:,.2f}")
              pdf.set_x(10)
              pdf.multi_cell(
                0,
                8,
                f"Best Month: {best_month.strftime('%B %Y')} "
                f"with revenue of {best_month_revenue.max():,.2f}")

              pdf.set_font("Helvetica", "B", 16)
              pdf.set_x(10)
              pdf.cell(0, 10, "Revenue Trend", ln=1)

              pdf.set_font("Helvetica", "", 11)
              pdf.set_x(10)

              if revenue_change is not None:
                if revenue_change >= 0:
                  pdf.multi_cell(
                    0, 8,
                   f"Revenue increased by {revenue_change:.2f}% "
                   f"from the previous month.")
        
                else:
                  pdf.multi_cell(
                    0, 8,
                    f"Revenue decreased by {abs(revenue_change):.2f}% "
                    f"from the previous month.")
        
           



              pdf.set_font("Helvetica", "B", 16)
              pdf.set_x(10)
              pdf.cell(0, 10, "Business insights", ln=1)

              pdf.set_font("Helvetica", "", 11)
              pdf.set_x(10)

              pdf.multi_cell(
                 0,
                 8,
                 f"Top Product: {top_product} generated "
                 f"{top_product_revenue:,.2f} in revenue.")


              if "Customer" in df_renamed.columns:
                pdf.set_x(10)
                pdf.multi_cell(
                 0,
                 8,
                  f"Top Customer: {top_customer} generated "
                  f"{top_customer_revenue:,.2f} in revenue.")

              if "Country" in df_renamed.columns:
                pdf.set_x(10)
                pdf.multi_cell(
                 0,
                 8,
                  f"Top Country: {top_country} generated "
                  f"{top_country_revenue:,.2f} in revenue.")

              if "Quantity" in df_renamed.columns:
                pdf.set_x(10)
                pdf.multi_cell(
                0,
                8,
                f"Top Product by Quantity: {product_quantity.index[0]} "
                f"sold {product_quantity.iloc[0]:,.0f} units.")

              if profit_available:
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_x(10)
                pdf.cell(0, 10, "Profit & Loss", ln=1)

                pdf.set_font("Helvetica", "", 11)
                pdf.set_x(10)
                pdf.multi_cell(
                  0, 8,
                  f"Total Profit: {total_profit:,.2f}")
    

                pdf.set_x(10)
                pdf.multi_cell(
                   0, 8,
                   f"Profit Margin: {profit_margin:.2f}%")
    

                pdf.set_x(10)
                pdf.multi_cell(
                0, 8,
                f"Products with Loss: {loss_products}")


    


    
                 
                
              
              

              

              




              



            #more PDF content will go here
           
              pdf_data = bytes(pdf.output())

              st.download_button(
                 label="Download",
                 data=pdf_data,
                 file_name="DataTally_Report.pdf",
                 mime="application/pdf")

           
            

             
             
        elif option == "Data Summary":
           st.subheader("Data Summary")

           total_records = df.shape[0]
           total_columns = df.shape[1]

           col1,col2 = st.columns(2)

           with col1:
              st.metric("Total Records:", total_records)


           with col2:
        
            st.metric("Total Columns", total_columns)   

        st.subheader("Product perfomance over time")   
        st.write( "This shows how each product's revenue changed from its first "
        "recorded month to its latest recorded month.")
        top_product_table = top_product_each_month.reset_index()
        #st.write(product_monthly_revenue)

        product_monthly_table = product_monthly_revenue.reset_index()
        top_product_each_month = (product_monthly_table.iloc[product_monthly_table.groupby("Date")["Revenue"].idxmax()])
        #st.dataframe(product_monthly_table) 

        product_month_count = (product_monthly_table.groupby("Product")["Date"].nunique().sort_values(ascending = False))
        #st.dataframe(product_month_count)

        product_monthly_table = product_monthly_table.sort_values("Date")
        product_revenue_change = (
           product_monthly_table.groupby("Product")["Revenue"].agg(first_month_revenue ="first", last_month_revenue="last"))
        #st.dataframe(product_revenue_change)

        product_revenue_change["Change"] = (product_revenue_change["last_month_revenue"]-product_revenue_change["first_month_revenue"])
        #st.dataframe(product_revenue_change)

        product_revenue_change["Change%"] =  (product_revenue_change["Change"]/product_revenue_change["first_month_revenue"]*100)
        st.dataframe(product_revenue_change)

        st.subheader("Top 5 Product")
        top_5_products = product_revenue.head(5)
        st.dataframe(top_5_products)
        top_5_revenue = top_5_products.sum()
        #st.write(top_5_revenue)
        top_5_percentage = (top_5_revenue / total_revenue) * 100
        #st.write(top_5_percentage)

        st.write(
         f"The top 5 products generated **{top_5_percentage:.1f}%** "
         f"of total revenue, indicating how strongly overall revenue depends "
         f"on the business's highest-performing products.")

        



       


               
               
                   
                   
     
               



                       
                        

               

     
              

            

        

    except Exception as e:
     st.error(f"Error: {e}")

        


