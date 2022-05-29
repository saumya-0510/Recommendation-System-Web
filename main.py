import time
from st_aggrid import GridOptionsBuilder, AgGrid
import streamlit as st
import pickle
import pandas as pd
from PIL import Image
from pyresparser import ResumeParser
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity

# Logo for the wep-app
img = Image.open('logo.jpg')

# Setting the configuration of the page
st.set_page_config(layout="wide", page_title='Job Recommendation', page_icon=img)

# Loading the pickled dataframes and models
jobs_naukri = pickle.load(open('data.pkl', 'rb'))
jobs_dice = pickle.load(open('dice_df.pkl', 'rb'))
label_for_splitting = pickle.load(open('label.pkl', 'rb'))
Xclass_for_splitting = pickle.load(open('xclass_for_splitting.pkl', 'rb'))
jobskills = pickle.load(open('jobskills.pkl', 'rb'))
svm_model = pickle.load(open('svm_model.pkl', 'rb'))
vectorizer = pickle.load(open('vectorizer_fit.pkl', 'rb'))

# Title of the web-app
st.title('Open Jobs Recommendation System')

# Styling the web-app
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Hiding the footer
hide_footer_style = """
        <style>
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_footer_style, unsafe_allow_html=True)


# Function for prediction of jobs based on skills
def SVM_prediction(skills_input):
    # Dividing training and testing data
    X_train, X_test, y_train, y_test = train_test_split(Xclass_for_splitting, label_for_splitting, test_size=0.2,
                                                        random_state=42)

    # Vectorize the input
    skills_vectorized = vectorizer.transform([skills_input.lower()])

    # Predict output based on vectorized input
    output = svm_model.predict(skills_vectorized)

    st.write("You may look into " + output[0] + " jobs.")
    st.write("Here is a list of jobs under " + output[0] + ":")
    cos = []

    # Getting the jobs within the field predicted
    labelData = jobs_dice[jobs_dice['Label'] == output[0]]

    for index, row in labelData.iterrows():
        skills = [row['skills']]
        skillVec = vectorizer.transform(skills)
        # Similarity judgement
        cos_lib = cosine_similarity(skillVec, skills_vectorized)
        cos.append(cos_lib[0][0])

    labelData['cosine_similarity'] = cos

    # Getting the most similar entries
    top = labelData.sort_values('cosine_similarity', ascending=False)

    # Styling the dataframe
    df_rec_top = top.rename(columns={'advertiseurl': 'URL of Ad',
                                     'company': 'Company',
                                     'employmenttype_jobstatus': 'Employment Type',
                                     'jobdescription': 'Job Description',
                                     'joblocation_address': 'Job Location',
                                     'jobtitle': 'Job Title',
                                     'skills': 'Skills required',
                                     'clean_jobtitle': 'Cleaned Job-title',
                                     'label': 'Label',
                                     'cosine_similarity': 'Similarity'})
    df_rec_top = df_rec_top.iloc[0:15, [1, 2, 4, 5]]
    gb = GridOptionsBuilder.from_dataframe(df_rec_top)
    gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
    gb.configure_side_bar()  # Add a sidebar
    gb.configure_selection('multiple', use_checkbox=True,
                           groupSelectsChildren="Group checkbox select children")  # Enable multi-row selection
    gridOptions = gb.build()
    with st.spinner('Please Wait'):
        time.sleep(3)
    st.success('Found Recommendations!')
    grid_response = AgGrid(
        df_rec_top,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        theme='streamlit',  # Add theme color to the table
        enable_enterprise_modules=True,
        height=350,
        width='100%'
    )


# Recommendation of jobs based on the inputs
def check(city, industry, experience, vacancies):
    return jobs_naukri.loc[(jobs_naukri['numberofpositions'] > vacancies)
                           & (jobs_naukri['joblocation_address'] == city)
                           & (jobs_naukri['Industry'] == industry)
                           & (jobs_naukri['Min Experience'] == experience)][[
        'company',
        'jobtitle',
        'Education',
        'payrate',
        'numberofpositions',
    ]]


# Getting industries related to your field
def related_industry(selected_industry):
    job = x[selected_industry]
    similar_jobs = x.corrwith(job)
    similar_jobs = similar_jobs.sort_values(ascending=False)
    similar_jobs = similar_jobs.iloc[2:]
    return similar_jobs.head(3)


# Displaying the first functionality
with st.container():
    st.container()
    with st.container():
        st.header('Recommendation through Details')
        with st.expander('See how it works'):
            st.write('You have to enter the details manually and then jobs will be recommended to you.')
        # Getting inputs
        city = st.selectbox(
            'Select the city:',
            list(jobs_naukri['joblocation_address'].value_counts().index)
        )
        industry = st.selectbox(
            'Select your industry:',
            list(jobs_naukri['Industry'].value_counts().index)
        )
        experience = st.selectbox(
            'Select your experience:',
            list(jobs_naukri['Min Experience'].value_counts().sort_values(ascending=False).index)
        )
        vacancies = st.slider(
            'How many vacancies are you looking for?',
            0, 10
        )

        if st.button('Recommend'):
            # Getting response from check function based on the inputs
            recommendations = check(city, industry, experience, vacancies)
            with st.spinner('Please Wait'):
                time.sleep(3)
            st.success('Found Recommendations!')
            df_rec = recommendations.rename(columns={'company': 'Company',
                                                     'jobtitle': 'Job Title',
                                                     'payrate': 'Salary',
                                                     'numberofpositions': 'No. of Positions available'})
            df_rec = df_rec.iloc[0:15, :]

            # Styling the dataframe
            gb = GridOptionsBuilder.from_dataframe(df_rec)
            gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
            gb.configure_side_bar()  # Add a sidebar
            gb.configure_selection('multiple', use_checkbox=True,
                                   groupSelectsChildren="Group checkbox select children")  # Enable multi-row selection
            gridOptions = gb.build()

            grid_response = AgGrid(
                df_rec,
                gridOptions=gridOptions,
                fit_columns_on_grid_load=True,
                theme='streamlit',  # Add theme color to the table
                enable_enterprise_modules=True,
                height=350,
                width='100%'
            )

            df_rec = grid_response['data']
            selected = grid_response['selected_rows']

# Horizontal line to mark division
st.markdown("""<hr style="height:5px;border:none;color:#393E46;background-color:#393E46;" /> """,
            unsafe_allow_html=True)

# Displaying the second functionality
st.container()

with st.container():
    st.header('Recommendation through Resume')
    with st.expander('See how it works'):
        st.write('Upload your resume to get job recommendations.')
    # Getting the resume
    uploaded_file = st.file_uploader("Choose a file (.pdf or .docx or .txt)")
    if st.button('Recommend Jobs'):
        if uploaded_file is not None:
            # Parsing the resume
            resume_data = ResumeParser(uploaded_file).get_extracted_data()
            string_skills = ','.join(map(str, resume_data['skills']))
            # Prediction of field and recommendation
            SVM_prediction(string_skills)

# Horizontal line to mark division
st.markdown("""<hr style="height:5px;border:none;color:#393E46;background-color:#393E46;" /> """,
            unsafe_allow_html=True)

# Displaying third functionality
with st.container():
    st.subheader('Recommend Related Industries:')
    # Cross tab between education and industry to identify related industries
    x = pd.crosstab(jobs_naukri['Education'], jobs_naukri['Industry'])

    # Getting input
    selected_industry = st.selectbox(
        'Select an Industry:',
        list(jobs_naukri['Industry'].value_counts().index)
    )
    if st.button('Show related industries'):
        # Showing related industries list
        related_industries_list = related_industry(selected_industry)
        st.write(related_industries_list)

# Horizontal line to mark division
st.markdown("""<hr style="height:5px;border:none;color:#393E46;background-color:#393E46;" /> """,
            unsafe_allow_html=True)

# Displaying trends and correlations between different fields
st.subheader('Analysis of Open Jobs')
col1, col2 = st.columns((3, 3))
col3, col4 = st.columns((4, 2))
col5, col6 = st.columns((3, 2))
with col1:
    st.image('Comparison of different jobs.png', 'Comparison of different jobs')
with col2:
    st.image('Distribution_of_experience.png', 'Distribution of experience')
with col3:
    st.image('Job vacancies on the basis of different factors.png', 'Job vacancies on the basis of different factors')
with st.container():
    with col4:
        st.image('Locations with high jobs.png', 'Locations w.r.t number of jobs')
        st.image('Vacancies for different degrees.png', 'Vacancies w.r.t Fields')
with col5:
    st.image('Companies providing jobs.png', 'Various Companies w.r.t Job openings')
with col6:
    st.image('Minimum experience required in each industry.png', 'Minimum Experience required in each Industry')
st.markdown("""---""")
