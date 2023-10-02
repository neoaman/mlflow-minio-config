import streamlit as st
import os

st.set_page_config (layout="wide")


with open("Readme.md",'r') as md:
    readme_lines = md.readlines()

# HACK Render the images

readme_buffer = []
images = [ "static/img/"+i for i in os.listdir("static/img")]
for line in readme_lines:
    readme_buffer.append(line)
    for image in images:
        if image in line:
            st.markdown(' '.join(readme_buffer[:-1]))
            st.image(image)
            readme_buffer.clear()
st.markdown('\n'.join(readme_buffer))