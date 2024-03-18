import streamlit as st
import PyPDF2
st.set_page_config(
    page_title="RESUMO SCOUT",
    layout="wide",
    menu_items={'About': "https://www.remostarts.com/"}
)
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')
from bokeh.models.widgets import Div
from streamlit_option_menu import option_menu
from st_on_hover_tabs import on_hover_tabs
import psycopg2
import os
import sys
import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import youtube_dl
def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    #converting the data of users in json file(Accessible in the Admin Side)
    json = df.to_json(orient="split")
    b64 = base64.b64encode(json.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()
    #close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("Here are some Courses and Certificates Recommendation for you")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 3)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

#DATABASE CONNECTION
connection = pymysql.connect(host='localhost', user='root', password='Aniket@007', database='remo')
cursor = connection.cursor()

#Inserting Data in the table(for Admin Side)
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

def run():
    st.markdown(
            '''<h1 style='text-align: center; color: black;'>RESUMO SCOUT</h1>''',
             unsafe_allow_html=True)
    #Creating Sidebar
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin", "Home"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")
    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    
    #Choosing among: User(to test resume), Admin(to get user data, can only be accessed by Admins) and Home(to redirect to Remostart Website)
    if choice == 'User':    
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)
                st.header("RESUME ANALYSIS")
                st.subheader("Your Basic Information")

                col1, col2, col3 = st.columns(3)
                with col1:
                    try:
                        st.text('\tEmail: ' + resume_data['email'])
                    except:
                        st.text("Can't detect E-mail!!")
                with col2: 
                    try:
                        st.text('Contact: ' + resume_data['mobile_number'])
                    except:
                        st.text("Can't detect phone number!!")
                with col3:
                    try:
                        st.text('\tResume pages: ' + str(resume_data['no_of_pages']))
                    except:
                        st.text("Can't detect Pages!!")

                st.subheader("Skills Recommendation")
                ## Dsiplay Skills
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')
                ##  Display Skill recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']
                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("According to our analysis, you're seeking for jobs in Data Science.")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #FF5733;'>Including these abilities on your CV will increase your chances of being hired.</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break
                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("According to our analysis, you're seeking for jobs in Web Development.")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #FF5733;'>Including these abilities on your CV will increase your chances of being hired.</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break
                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("According to our analysis, you're seeking for jobs in Android App Development.")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #FF5733;'>Including these abilities on your CV will increase your chances of being hired.</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break
                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("According to our analysis, you're seeking for jobs in IOS App Development.")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #FF5733;'>Including these abilities on your CV will increase your chances of being hired.</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break
                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("According to our analysis, you're seeking for jobs in UI-UX Development.")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #FF5733;'>Including these abilities on your CV will increase your chances of being hired.</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break
                ### Rating the resume and providing some suggestions to improve
                st.subheader("**Let's check how good your Resume is!!**")            
                resume_score = 0
                if 'Objective' or'OBJECTIVE' or 'Career Objective' or 'CAREER OBJECTIVE' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Career Objective.</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include your Career Objective as this will help recruiters understand what you are seeking.</h4>''',
                        unsafe_allow_html=True)

                if 'Certificates' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Certificates and Interests.</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include your Certificates and Interests as this will help recruiters understand your field of expertise.</h4>''',
                        unsafe_allow_html=True)

                if 'Technical Skills' or 'Skills' or 'TECHNICAL SKILLS' or 'SKILLS' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Skills. </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include the skills you have aquired by far as this will help recruiters to understand your field of expertise.</h4>''',
                        unsafe_allow_html=True)

                if 'Soft Skills' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Soft Skills. </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include the Soft Skills as it shows how you will react under pressure, or what is your professional potential.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' or 'PROJECTS' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Projects.</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Kindly include Projects. It will demonstrate whether or not you handled the work relevant to the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'EXPERIENCE' or 'Experience' or 'EXPERIENCES' or 'Experiences' in resume_text:
                    resume_score = resume_score + 15
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Experience.</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include the Experience you have aquired by far as it highlights the most relevant abilities you bring in two to three phrases..</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 10
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>🟢 Fabulous! You've included your Achievements and Awards.</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: red;'>🔴 Please include the Achievements and Awards you have aquired by far as it highlights the most relevant abilities you bring in two to three phrases..</h4>''',
                        unsafe_allow_html=True)     

                st.subheader("Your Resume Score is: ")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;}
                    </style>""",
                    unsafe_allow_html=True
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('Your Resume Writing Score: ' + str(score))
                connection.commit()
            else:
                st.error('OOPS!!! Something went wrong!!')
    
## Admin Side(Admin can get the data of users)
    elif choice == "Admin":
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Remostart' and ad_password == 'Remostart123':
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.json', 'Download Report'), unsafe_allow_html=True)
            else:
                st.error("Wrong ID & Password Provided")
                
#Home Side(This will redirect the user to official website of Remostart)
    elif choice == "Home":
        js = "window.open('https://www.remostarts.com/')"  # New tab or window
        html = '<img src onerror="{}">'.format(js)
        div = Div(text=html)
        st.bokeh_chart(div)

run()