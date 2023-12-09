import os
from os.path import join as fullfile
import copy
import json


CONFIG_PATH = './config'
CONFIG_NAME = 'subjects'

subjects = None
current_subject = None

def get_all():
    global subjects, current_subject
    if subjects is None:
        subjects, current_subject = load_subjects()
    return copy.deepcopy(subjects)


def get_current():
    global subjects, current_subject
    subjects = get_all()
    return copy.deepcopy(current_subject)


def set_current_subject(subject):
    global current_subject
    current_subject = copy.deepcopy(subject)
    save()


def load_subjects():
    subjects = []
    current_subject = None
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            res = json.load(f)
            subjects = [Subject(**item) for item in res['subjects']]
            for s in subjects:
                if s.no == res['current_subject']:
                    current_subject = copy.deepcopy(s)
                    break
    return subjects, current_subject


def update(subject):
    global subjects
    subjects = get_all()
    for s in subjects:
        if s.no == subject.no:
            s.update(subject)
            save()
            break


def insert(new_subject):
    global subjects
    subjects = get_all()
    exist = False
    for s in subjects:
        if s.no == new_subject.no:
            exist = True
            s.update(new_subject)
            save()
            break
    if not exist:
        subjects.append(new_subject)
        save()


def delete(subject):
    global subjects
    subjects = get_all()
    subjects = list(filter(lambda x: x.no == subject.no, subjects))
    save()


def save():
    global subjects, current_subject
    config_path = get_config_path()

    folder_path = os.path.dirname(config_path)
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
        except:
            pass

    with open(config_path, 'w') as f:
        json.dump({
            'current_subject': current_subject.no if current_subject is not None else '',
            'subjects': [{
                'no': s.no,
                'name': s.name,
                'gender': s.gender,
                'age': s.age,
                'height': s.height,
                'weight': s.weight,
        } for s in subjects]}, f)


def get_config_path():
    return fullfile(CONFIG_PATH, CONFIG_NAME + '.json')


class Subject:
    def __init__(self, no='', name='', gender='', age=-1, height=-1, weight=-1):
        self._no = no
        self._name = name
        self._gender = gender
        self._age = age
        self._height = height
        self._weight = weight

    def update(self, subject):
        self.no = subject.no
        self.name = subject.name
        self.gender = subject.gender
        self.age = subject.age
        self.height = subject.height
        self.weight = subject.weight

    @property
    def no(self):
        return self._no

    @no.setter
    def no(self, new_no):
        self._no = new_no

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, new_gender):
        self._gender = new_gender

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, new_age):
        self._age = new_age

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, new_height):
        self._height = new_height

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, new_weight):
        self._weight = new_weight

    def __eq__(self, s):
        return s.no == self.no and s.name == self.name and s.gender == self.gender and s.age == self.age and s.height == self.height and s.weight == self.weight

