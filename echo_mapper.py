import streamlit as st
import pandas as pd
from string import ascii_uppercase
from datetime import datetime
from copy import deepcopy
from streamlit_bokeh import streamlit_bokeh
from plate_viz import plate_viz

# Echo525 Standard column name: [Sample ID,Source Plate,Source Well,Destination Plate,Destination Well,Volume]

def app():    
    def split_comma(text):
        tmp = [x.strip() for x in text.split(',')]
        return list(filter(lambda x:bool(x), tmp))
    
    def check_advanced_split(base):
        if base == "None":
            return True
        
        name_list = split_comma(input_name)
        
        if base == "Row":
            if len(split_comma(row_numbers)) == len(name_list):
                return True
            else:
                return False
        elif base == "Col":
            if len(split_comma(col_numbers)) == len(name_list):
                return True
            else:
                return False
    
    def mapping_dict(row_list: list, col_list: list, name_list, volume, base_config):
        tmp = dict()
        tmp['Destination Well'] = []
        tmp['Volume'] = []
        tmp['Sample ID'] = []
        
        if base_config == 'None':
            name = name_list[0]
            for col in col_list:
                for row in row_list:
                    tmp['Destination Well'].append(col+row)
                    tmp['Volume'].append(volume)
                    tmp['Sample ID'].append(name)
            return tmp

        if base_config == 'Row':
            for row, name in zip(row_list, name_list):
                for col in col_list:
                    tmp['Destination Well'].append(col+row)
                    tmp['Volume'].append(volume)
                    tmp['Sample ID'].append(name)
            return tmp
        
        if base_config == 'Col':
            for col, name in zip(col_list, name_list):
                for row in row_list:
                    tmp['Destination Well'].append(col+row)
                    tmp['Volume'].append(volume)
                    tmp['Sample ID'].append(name)
            return tmp
    
    def empty_plate_df(plate_type='384'):
        if plate_type == '384':
            rows= ascii_uppercase[:16]
            columns = [str(i) for i in range(1, 25)]
            
            long_columns = ['value']
            long_rows = [i+j for j in columns for i in rows]

            plate_df = pd.DataFrame(index=long_rows, columns=long_columns)
            plate_df.index.name = 'well'
            
            return plate_df
        
        if plate_type == '96':
            rows = ascii_uppercase[:8]
            columns = [str(i) for i in range(1, 13)]     
            
            long_columns = ['value']
            long_rows = [i+j for j in columns for i in rows]
            
            plate_df = pd.DataFrame(index=long_rows, columns=long_columns)
            plate_df.index.name = 'well'
            return plate_df
    
    @st.cache_data    
    def unmapped_input(source_list, mapped_list):
        return [value for value in source_list if value not in mapped_list]
    
    def download_format(source_df: pd.DataFrame, input_plate: pd.DataFrame):
        mapped_dict = input_plate['value'].dropna().to_dict()
        new_dict = dict()
        for key, value in mapped_dict.items():
            if value in new_dict.keys():
                assert f"Duplicate Error: {value} is already in input_plate"
            new_dict[value] = key
        picklist = deepcopy(source_df)
        for name in source_df['Sample ID'].unique():
            if name not in new_dict.keys(): # Skipped non mapped value
                continue
            picklist.loc[source_df['Sample ID'] == name, 'source_well'] = new_dict[name]
        
        picklist['Source Plate'] = plate_name
        picklist['Destination Plate'] = 'destination'
        
        column_order = ['Sample ID', 'Source Plate', 'source_well', 'Destination Plate', 'Destination Well', 'Volume']
        picklist = picklist[column_order]
        
        st.session_state.picklist = picklist
    
    def file_upload():
        if st.session_state.upload_file:
            df = pd.read_csv(st.session_state.upload_file)
            for col in ['Sample ID', 'Destination Well' ,'Volume']:
                if col not in df.columns:
                    st.warning(f"Uploaded file Error: {col} is not in uploaded Dataframe")
                    st.stop()
            
            st.session_state.result_df = df[['Sample ID', 'Destination Well', 'Volume']]
            if len(st.session_state.result_df) > 0:
                st.session_state.graph = cache_graph(st.session_state.result_df)
    
    def cache_graph(result_df):        
        grouped = result_df.groupby('Destination Well')
        content = (
            grouped[['Sample ID', 'Volume']]
            .apply(lambda g: g.groupby('Sample ID')['Volume'].sum().to_dict())
        )
        count = grouped.size()
        content_df = pd.DataFrame({
            'well': content.index,
            'content': content.values,
            'count': count.values
        })
        
        return plate_viz(content_df)

    # Session
    if 'result_df' not in st.session_state:
        st.session_state.result_df = pd.DataFrame({'Sample ID':[], 'Destination Well':[], 'Volume': []})
    if 'input_plate' not in st.session_state:
        st.session_state.input_plate = empty_plate_df()
    if 'unmapped_list' not in st.session_state:
        st.session_state.unmapped_list = []
    if 'picklist' not in st.session_state:
        st.session_state.picklist = pd.DataFrame()
    if 'graph' not in st.session_state:
        st.session_state.graph = None
    
    # Front
    st.write(
        """
        # Echo mapper
        """
    )
    """
    - When you enter `Append` button, the same input is entered into all selected areas (combinations of row and col).
    - When you select multiple inputs in the Advanced check, you can enter them into the selected areas separately. (Input criteria selection)
        - The number of inputs and the number of rows and columns to be used as criteria must be the same.
    """
    with st.container(border=True):
        st.file_uploader("Upload input plate", on_change=file_upload, type=['csv'], key='upload_file', help='Input data should have specific columns, Sample ID, Destination Well, Volume')
        col1 = st.columns([1,1,2])
        
        row_start = col1[0].number_input('row_st', value=1, step=1, min_value=1, max_value=8)
        row_end = col1[1].number_input('row_end', value=1, step=1, min_value=1, max_value=8)
        row_numbers = col1[2].text_input('Edit rows', value=','.join([ascii_uppercase[i-1] for i in range(row_start, row_end+1)]), help="separator: ,")
        
        col_start = col1[0].number_input('col_st', value=1, step=1, min_value=1, max_value=12)
        col_end = col1[1].number_input('col_end', value=1, step=1, min_value=1, max_value=12)
        col_numbers = col1[2].text_input('Edit cols', value=','.join([str(i) for i in range(col_start, col_end+1)]), help="separator: ,")
        
        col2 = st.columns([1,1])
        volume = col2[0].number_input("Volume (nl)", value=100, step=20, key='general_vol')
        
        input_name = st.text_input("Sample name", key='general_name', value='sample1', help='separator: ,')
    
    with st.expander("Advanced", expanded=False):
        ad_base = st.selectbox('Separate Input by', options=['None', 'Row', 'Col'], key='base_config')
        
        if check_advanced_split(ad_base):
            st.success("")
        else:
            st.warning("Missmatch Error: Check the number of inputs and the number of rows and columns")
        
    if st.button("Append", type='primary'):
        tmp = pd.DataFrame(mapping_dict(split_comma(col_numbers), split_comma(row_numbers), split_comma(input_name), volume, base_config=ad_base))
        st.session_state.result_df = pd.concat([st.session_state.result_df, tmp], axis=0, ignore_index=True)
        
        if len(st.session_state.result_df) > 0:
            st.session_state.graph = cache_graph(st.session_state.result_df)
    
    if st.session_state.graph:
        streamlit_bokeh(st.session_state.graph, use_container_width=False)
    with st.expander("Result Table", expanded=True):
        
        st.dataframe(st.session_state.result_df, use_container_width=True, hide_index=True)
    
    with st.container(border=True):
        plate_name = st.text_input("Source plate name", value="source_plate")
        mapped = st.data_editor(st.session_state.input_plate, use_container_width=True)
        st.session_state.unmapped_list = unmapped_input(source_list= st.session_state.result_df['Sample ID'].unique(),
                                                        mapped_list= mapped.dropna().value.unique())
        st.text_area("unmapped input", value=', '.join(st.session_state.unmapped_list), disabled=True, help='The unmapped input must be mapped to the source plate')
    
    if st.button("Generate Picklist",
                 on_click=download_format,
                 disabled=bool(len(st.session_state.unmapped_list)),
                 kwargs={'source_df': st.session_state.result_df,
                         'input_plate': mapped},
                 help='Check parameters and generate Download button'):
        # Check parameters
        st.download_button('Download to CSV', data=st.session_state.picklist.to_csv(index=False), 
                        file_name=f"{datetime.now().strftime('%y_%m_%d_%s')}_echo.csv")
        
    # Check Error
    # - Input name duplication in input plate
if __name__ == '__main__':
    app()