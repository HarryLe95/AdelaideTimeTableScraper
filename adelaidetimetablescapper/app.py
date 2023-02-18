from bs4 import BeautifulSoup
import requests 
from dataclasses import dataclass
from typing import Sequence, Any

home_url = "https://access.adelaide.edu.au/courses"
base_url = "https://access.adelaide.edu.au/courses/search.asp"

CLASSTYPE = {"LE":"Lecture", "WR": "Workshop", "PR": "Practical", "PJ": "Project", "TU": "Tutorial"}

@dataclass
class Subject:
    term: str
    catalogue: str 
    title: str 
    unit: int 
    career: str 
    campus: str 
    url: str 
    
    def __repr__(self):
        return self.title

@dataclass 
class Date:
    date: str
    day: str 
    time: str 
    location: str 
    
    def __repr__(self):
        return self.date

@dataclass 
class Class: 
    number: int
    section: str 
    size: int 
    available: int 
    dates: Sequence[Date] 
    
    def __repr__(self):
        return self.number 

@dataclass 
class ClassSchedule:
    classes: Sequence[Class]
    
    def __post_init__(self):
        self.get_class_type()

    @staticmethod 
    def _get_class_type(item: Class)->str:
        return CLASSTYPE[item.section[:2]]
    
    def __repr__(self) -> str:
        repr = "{"
        for index, (k,v) in enumerate(self._classes.items()):
            repr += f"{k}: {v}"
            if index != len(self._classes) - 1:
                repr+= ", "
        repr += "}"
        return repr 
    
    def get_class_type(self):
        self._classes = {}
        if len(self.classes) != 0: 
            for item in self.classes: 
                class_type = self._get_class_type(item)
                if class_type in self._classes: 
                    self._classes[class_type].append(item)
                else:
                    self._classes[class_type] = [item]
                    

def validate_response(response: requests.models.Response)->None: 
    if response.status_code != requests.codes.ok: 
        response.raise_for_status()

def get_subject_area_url(area:str, year:int=2023)->str:
    if " " in area: 
        area = area.replace(" ", "+")
    return f"{base_url}?year={year}&m=r&subject={area}"

def get_all_subject_areas()->dict[str,str]:
    # Enter base url
    response = requests.get(base_url)
    validate_response(response)
    html_content = response.text
    
    # Parse html content
    soup = BeautifulSoup(html_content, "html5lib")
    basic_table = soup.find("table", attrs={"id":"basic"})
    options = basic_table.find_all("option")
    return {x['value']: x.string for x in options if x['value']!=''}

def get_area_courses(area:str)->dict[str, Subject]:
    courses = {}
    # Enter Course Search page
    url = get_subject_area_url(area)
    response = requests.get(url)
    validate_response(response)
    
    # Parse html content
    html_content = response.text
    soup = BeautifulSoup(html_content, "html5lib") 
    content_div = soup.find("div", attrs={"class":"content"})
    table_body = content_div.find("p")
    table_rows = table_body.find_all("tr")
    for index, row in enumerate(table_rows): 
        if index == 0:
            continue 
        data = row.find_all("td")
        term = str(data[0].string).strip()
        catalogue = data[1].string 
        title = data[2].string 
        href = data[2].find('a')['href']
        unit = int(data[3].string)
        career = data[4].string 
        campus = data[5].string 
        subject = Subject(term=term, catalogue=catalogue, title=title, 
                          unit=unit, career=career, campus=campus, url=href)
        courses[f"{term} {catalogue} {campus}"] = subject 
    return courses
        
def get_course_timetable(course: Subject|str)->ClassSchedule:
    classes = []
    if isinstance(course, Subject):
        response = requests.get(f"{home_url}/{course.url}")
    else:
        response = requests.get(course)
    validate_response(response)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html5lib")
    table_rows = soup.find("div",attrs={"id":"hidedata04_1"}).find_all("tr")
    
    current_class = None 
    for row in table_rows:
        # Header sections - skip 
        if row.find("th") is not None: 
            continue 
        
        # Data section - first 
        table_data = row.find_all("td")
        if row.has_attr("class"):
            if row['class'] == ['data']:
                if current_class is not None:
                    classes.append(current_class)
                number = table_data[0].string
                section = table_data[1].string
                size = table_data[2].string 
                available = table_data[3].string 
                date = table_data[4].string 
                day = table_data[5].string 
                time = table_data[6].string 
                location = table_data[7].string 
                dates = [Date(date=date, day=day, time=time,location=location)]
                current_class = Class(number, section, size, available, dates)
        # Data section - subsequent
        else:
            if len(table_data)==1:
                continue 
            date = table_data[0].string 
            day = table_data[1].string 
            time = table_data[2].string 
            location = table_data[3].string 
            dates = Date(date=date, day=day, time=time,location=location)
            current_class.dates.append(dates)
    # Dump the last time 
    classes.append(current_class)
    return ClassSchedule(classes)
    

if __name__ == "__main__":
    # areas = get_all_subject_areas()
    # courses = get_area_courses("MINING")
    classes = get_course_timetable("https://access.adelaide.edu.au/courses/details.asp?year=2023&course=108960+1+4310+1")
    print("End")