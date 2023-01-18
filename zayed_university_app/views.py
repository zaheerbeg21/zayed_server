from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import re
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from spacy_langdetect import LanguageDetector
import spacy
from spacy.tokens import Doc, Span
from googletrans import Translator
from spacy.language import Language
from .models import Log, EventType
from difflib import SequenceMatcher
import json
import xml.etree.ElementTree as ET
import requests
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import render_to_pdf
from django.http import HttpResponse
from django.views.generic import View
import xlwt
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from autocorrect import Speller
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse
import pandas as pd
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

_stop_words = stopwords.words('english')
_stop_words_ar = stopwords.words('arabic')


def remove_custom(_char, _list):
    for i in _list:
        try:
            _list.remove(_char)
        except:
            pass

    return _list


def get_file_data(filename):
    if ".xml" in filename:
        tree = ET.parse(filename)
        root = tree.getroot()

        sys_folder = [elem for elem in root.iter("system-folder")]
        sys_page = [elem for elem in root.iter("system-page")]
        sys_file = [elem for elem in root.iter("system-file")]

        sys_folder_list = []
        for child in sys_folder:
            try:
                sys_folder_list.append(
                    [child.find('title').text, "https://www.zu.ac.ae/main" + child.find('path').text])
            except:
                sys_folder_list.append(
                    [child.find('name').text, "https://www.zu.ac.ae/main" + child.find('path').text])

        sys_page_list = []
        for child in sys_page:
            try:
                sys_page_list.append(
                    [child.find('title').text, "https://www.zu.ac.ae/main" + child.find('path').text])
            except:
                sys_page_list.append(
                    [child.find('name').text, "https://www.zu.ac.ae/main" + child.find('path').text])

        sys_file_list = []
        for child in sys_file:
            try:
                sys_file_list.append(
                    [child.find('title').text, "https://www.zu.ac.ae/main" + child.find('path').text])
            except:
                sys_file_list.append(
                    [child.find('name').text, "https://www.zu.ac.ae/main" + child.find('path').text])

        return ['xml', sys_folder_list, sys_page_list, sys_file_list]

    elif ".json" in filename:
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)
            _data = []
            for i in data:
                try:
                    service_name = i['ServiceName']
                    generated_link = i['GeneratedLink']
                    _data.append([service_name, generated_link])

                except:
                    for i in data['assets']:
                        try:
                            title = i['title']
                            path = i['path']
                            _data.append(
                                [title, "https://www.zu.ac.ae/main" + path])
                        except:
                            pass

        return ['json', _data]


def string_similarity(str1, str2):
    result = SequenceMatcher(a=str1.lower(), b=str2.lower())
    return result.ratio()


def get_ratios(_input_list_, _sys_, _main_list):
    for i in _input_list_:
        for j in _sys_:
            name = j[0]
            if i.upper().strip() in name.upper().strip() or i.upper().strip() == name.upper().strip():
                _main_list.append([string_similarity(i, name), j])

    return _main_list


def list_to_str(_list):
    _str = ""
    if len(_list) > 1:
        for i in _list:
            if i == _list[-1]:
                _str += i

            else:
                _str += i + " "

    return _str


workspace_id = 'lMpsX8-ivT4J5jaAZRo4cNUnotfqOO-_Vp2zia532An5'
workspace_url = 'https://api.eu-gb.assistant.watson.cloud.ibm.com/instances/dbb25da5-56bd-4b0c-ac66-62db88b266a6'
assistant_id_eng = '20a3ca09-8ae6-4c62-ae83-b9f9d1f7e394'
assistant_url = 'https://api.eu-gb.assistant.watson.cloud.ibm.com/instances/dbb25da5-56bd-4b0c-ac66-62db88b266a6'
assistant_id_ar = '67525f3e-6b3d-4474-a957-dfe0ee55730f'
assistant_id_crawl = '498b1e0a-15c0-47c9-9204-829053559b00'
assistant_crawl_json_id = '4c8f53fc-7293-43dd-970c-fba16887b8b2'

cont = {}
translator = ''
# assistant = ''
session_id_ = ''
spell = Speller(lang='en')


def create_lang_detector(nlp, name):
    return LanguageDetector()


Language.factory("language_detector", func=create_lang_detector)
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('language_detector', last=True)


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


global assistant
authenticator = IAMAuthenticator(workspace_id)
assistant = AssistantV2(version='2021-06-14', authenticator=authenticator)
assistant.set_service_url(assistant_url)


def get_data(_dict):
    return _dict['event_type'], _dict['event_question'], _dict['user_email']


def string_similarity(str1, str2):
    result = SequenceMatcher(a=str1.lower(), b=str2.lower())
    return result.ratio()


@csrf_exempt
def get_response_from_watson(request):
    _data = JSONParser().parse(request)
    ip = request.META.get('REMOTE_ADDR')

    try:
        event_type, text, user_email = get_data(_data)
        session_id_ = _data['session_value']
    except:
        text = ''
        session_id_ = ''

    print('RIGHT SPELLING', spell(text), _data['spell_check_bool'], _data['spell_check_bool'] == True)
    if spell(text) != text and _data['spell_check_bool'] == True:
        return JsonResponse({'session_id': session_id_, 'answer': f'{spell(text)}', 'intent': 'spell'})

    doc = nlp(text.upper())

    if session_id_ == '' and doc._.language['language'] == 'ar':
        session_id_ = assistant.create_session(
            assistant_id_ar).get_result()['session_id']
        response = assistant.message(assistant_id=assistant_id_ar, session_id=session_id_, input={'text': text},
                                     context=cont)
    else:
        session_id_ = assistant.create_session(
            assistant_id_eng).get_result()['session_id']
        response = assistant.message(assistant_id=assistant_id_eng, session_id=session_id_, input={'text': text},
                                     context=cont)
        print("assistant_id_eng")

    res = response.get_result()
    # print('RESPONSE ', res)

    try:
        res_conf = res['output']['intents'][0]['confidence']
        print("CONF", res_conf)
    except:
        try:
            res_conf = res['output']['generic'][0]['primary_results'][0]['result_metadata']['confidence']
            print("--", res_conf)
        except:
            res_conf = 0 if res['output']['generic'][0]['header'] == "I searched my knowledge base, but did not find anything related to your query." else 0
            print("---", res_conf)
    print(len(res['output']['intents']) > 0, res_conf > 0.85)
    if len(res['output']['intents']) > 0 and res_conf > 0.85:
        intents = res['output']['intents'][0]['intent']
        print("intents", intents)
    else:
        intents = ""
        print("Empty Intent")
        
        _text = text.lower()
        _text = text.lower().replace('zayed', '').replace('university', '')

        _input_list = text.split(' ')

        _input_list = remove_custom('i', _input_list)
        _input_list = remove_custom('a', _input_list)

        for i in _input_list:
            for j in _stop_words:
                if i.upper().strip() == j.upper().strip():
                    _text = _text.replace(i, "")
        
        for i in _input_list:
            for j in _stop_words_ar:
                if i.upper().strip() == j.upper().strip():
                    _text = _text.replace(i, "")

        _main_input = _text.split(" ")
        _main_input_list = [i for i in _main_input if i]

        _main_input_list = remove_custom('i', _main_input_list)
        _main_input_list = remove_custom('a', _main_input_list)

        main_df = pd.DataFrame()
        for root, dir, files in os.walk(f'zayed_university_app{os.sep}datainfor_files'):
            for _file in files:
                data = get_file_data(os.path.join(root, _file))

                if data[0] == "xml":
                    sys_folder = data[1]
                    sys_page = data[2]
                    sys_file = data[3]

                    all_xml = []

                    all_xml = get_ratios(_main_input_list, sys_folder, all_xml)
                    all_xml = get_ratios(_main_input_list, sys_page, all_xml)
                    all_xml = get_ratios(_main_input_list, sys_file, all_xml)

                    _main_input_string = list_to_str(_main_input_list)
                    
                    links_ratio = []
                    for i in all_xml:
                        links_ratio.append([i[0], string_similarity(i[1][0], _main_input_string), i[1][0], i[1][1]])
                    
                    df1 = pd.DataFrame(links_ratio, columns=['single_ratio', 'actual_ratio', 'name', 'path'])
                    main_df = main_df.append(df1, ignore_index=True)

                if data[0] == "json":
                    json_data = data[1]

                    all_json = []
                    all_json = get_ratios(_main_input_list, json_data, all_json)

                    _main_input_string = list_to_str(_main_input_list)
                    
                    links_ratio = []
                    for i in all_json:
                        links_ratio.append([i[0], string_similarity(i[1][0], _main_input_string), i[1][0], i[1][1]])
                    
                    df1 = pd.DataFrame(links_ratio, columns=['single_ratio', 'actual_ratio', 'name', 'path'])
                    main_df = main_df.append(df1, ignore_index=True)
        
        main_df = main_df.drop_duplicates(subset="path", keep="last")
        top_df1 = main_df.sort_values('actual_ratio', ascending=False).head(5).values.tolist()
        top_df1 = top_df1 = [i[3] if ".pdf" in i[3] else i[3] + ".aspx" for i in top_df1]

        df1_str = ""
        for i in top_df1:
            df1_str += i + "\n"
        print("df1_str", df1_str)

        if len(top_df1) > 0:
            return JsonResponse({'session_id': session_id_, 'answer': df1_str, 'intent': 'General', 'url': top_df1})

        else:
            eid = EventType.objects.get(id=int(5))
            Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                               event_answer='', intent='General')
            return JsonResponse(
                {'session_id': session_id_,
                    'answer': "Sorry, I am not able to detect the language you are asking."})

    try:
        output = res['output']['generic'][0]['primary_results'][0]['highlight']['answer']
    except:
        try:
            output = res['output']['generic'][0]['additional_results'][0]['highlight']['answer']
        except:
            try:
                output = res['output']['generic'][0]['text']
                print("OUTPUT", output, intents)
                if intents.lower() == "greetings" or intents.lower() == "start_greetings" or intents.lower() == "end_greetings" or intents.lower() == "live_agent":
                    return JsonResponse({'session_id': session_id_, 'answer': output, 'intent': intents})
            except:
                print("In 3rd Except")
                eid = EventType.objects.get(id=int(5))
                Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                                   event_answer='', intent=intents)
                return JsonResponse(
                    {'session_id': session_id_,
                     'answer': "Sorry, I am not able to detect the language you are asking."})

    if len(output) > 1:
        temp = ''
        for o in output:
            temp += o + ' '
        message = cleanhtml(temp)

    else:
        message = cleanhtml(output[0])
    if message == '':
        message = cleanhtml(res['output']['generic'][0]
                            ['primary_results'][0]['answers'][0]['text'])
    message = cleanhtml(message)
    eid = EventType.objects.get(id=int(event_type))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                       event_answer=message, intent=intents)
    return JsonResponse({'session_id': session_id_, 'answer': message, 'intent': intents})

@csrf_exempt
def login(request):
    _data = JSONParser().parse(request)
    event_type, event_question, user_email = get_data(_data)
    ip = request.META.get('REMOTE_ADDR')
    intents = _data['intent']
    eid = EventType.objects.get(id=int(event_type))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer='', intent=intents)

    return JsonResponse({'status': 'success'})


@csrf_exempt
def wrong_answer(request):
    _data = JSONParser().parse(request)
    event_type, event_question, user_email = get_data(_data)
    ip = request.META.get('REMOTE_ADDR')
    event_answer = _data['event_answer']
    intents = _data['intent']
    eid = EventType.objects.get(id=int(3))
    print('[INFO]', event_type, event_question, user_email,
          ip, event_answer, intents, eid.description)
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer=event_answer, intent=intents)

    return JsonResponse({'status': 'success'})


@csrf_exempt
def reset_count(request):
    _data = JSONParser().parse(request)
    event_type, event_question, user_email = get_data(_data)
    ip = request.META.get('REMOTE_ADDR')
    event_answer = _data['event_answer']
    intents = _data['intent']
    eid = EventType.objects.get(id=int(event_type))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer=event_answer, intent=intents)

    return JsonResponse({'status': 'success'})


def is_valid_queryparam(param):
    return param != '' and param is not None


# Common Global variable
log_exp = None


@login_required
def advance_filter(request):
    depart_name = request.session['depart']
    global log_exp

    if depart_name != 'SuperAdmin':
        log_ = Log.objects.filter(
            intent=depart_name).order_by('-user_datetime')
    else:
        log_ = Log.objects.all().order_by('-user_datetime')

    event_type_id_exact_query = request.GET.get('etype')
    print("type = ", type(event_type_id_exact_query))
    user_email = request.GET.get('email')
    event_question = request.GET.get('quest')
    event_answer = request.GET.get('ans')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    intent_exact_query = request.GET.get('dtype')

    if is_valid_queryparam(event_type_id_exact_query):
        log_ = log_.filter(event_type_id=event_type_id_exact_query)

    if is_valid_queryparam(user_email):
        log_ = log_.filter(user_email__icontains=user_email)

    if is_valid_queryparam(event_question):
        log_ = log_.filter(event_question__icontains=event_question)

    if is_valid_queryparam(event_question):
        log_ = log_.filter(event_question__icontains=event_question)
    if is_valid_queryparam(event_answer):
        log_ = log_.filter(event_answer__icontains=event_answer)

    if is_valid_queryparam(date_min):
        log_ = log_.filter(user_datetime__gte=date_min)

    if is_valid_queryparam(date_max):
        log_ = log_.filter(user_datetime__lte=date_max)

    if is_valid_queryparam(intent_exact_query):
        log_ = log_.filter(intent=intent_exact_query)

    dept = Log.objects.all().values_list('intent', flat=True).distinct()
    dept_list = [i for i in dept if i != '']

    event_ = EventType.objects.all()
    # event_list = [i for i in event_ if i != '']
    # print("event_type_id>>> ", event_.description)

    log_exp = log_

    context = {
        'log_': log_,
        'dept_list': dept_list,
        'event_': event_,
        'depart_name': depart_name,
        'admin_type': request.session['admin_type'],

        'event_type_id_exact_query': event_type_id_exact_query,
        'user_email': user_email,
        'event_question': event_question,
        'event_answer': event_answer,
        'date_min': date_min,
        'date_max': date_max,
        'intent_exact_query': intent_exact_query

    }

    return render(request, 'home/advance_filter.html', context)


# Opens up page as PDF
class ViewPDF(LoginRequiredMixin, UserPassesTestMixin, View):

    def get(self, request, *args, **kwargs):
        context = {
            'log_': Log.objects.all()
        }

        pdf = render_to_pdf('home/filter_template.html', context)
        if pdf:
            return HttpResponse(pdf, content_type='application/pdf')
        return HttpResponse("PDF Not Found.")

    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return False


def admin_check(user):
    if user.is_staff or user.is_superuser:
        return True
    return False


@login_required
@user_passes_test(admin_check)
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Event ID', 'User Email', 'Question', 'Answer',
               'Date Time', 'Department']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = Log.objects.all().values_list(
        'event_type_id__description', 'user_email', 'event_question',
        'event_answer', 'user_datetime', 'intent')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    if wb:
        return response
    return HttpResponse("No Data Found.")


# # Automatically downloads Filtered PDF file
# class FilterPDF(LoginRequiredMixin, View):

#     def get(self, request, *args, **kwargs):
#         global log_exp

#         context = {
#             'log_': log_exp,
#         }
#         pdf = render_to_pdf('home/filter_template.html', context)
#         if pdf:
#             return HttpResponse(pdf, content_type='application/pdf')
#         return HttpResponse("PDF Not Found.")

# Automatically downloads Filtered PDF file
class FilterPDF(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        global log_exp
        len_log = len(log_exp)
        temp_l = []

        for i in log_exp:
            if 'http' in i.event_answer:
                i = i.event_answer.split()
                # print(">> ", i)
                tmp_str = ''
                for i_ in i:
                    temp_i = ''
                    if i_.startswith('http') and len(i_) > 45:
                        while len(i_) > 45:
                            # print("in while 45", i_)
                            temp_i += i_[:45] + '\n'
                            i_ = i_[45:]
                        if len(i_) > 0:
                            temp_i += i_
                        tmp_str += '\n' + temp_i + ''
                    else:
                        tmp_str += i_ + ' '
                    # print("after if-else", tmp_str)
                temp_l.append(tmp_str.strip())
            else:
                temp_l.append(i.event_answer)

        context = {
            'len_log': len_log,
            'log_': log_exp,

            'zip_': zip(log_exp, temp_l)
        }
        pdf = render_to_pdf('home/filter_template.html', context)
        if pdf:
            return HttpResponse(pdf, content_type='application/pdf')
        return HttpResponse("PDF Not Found.")


# Automatically downloads Filtered Excel file
@login_required
def filter_excel(request):
    global log_exp
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Event ID', 'User Email', 'Question', 'Answer',
               'Date Time', 'Department']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = log_exp.values_list(
        'event_type_id__description', 'user_email', 'event_question',
        'event_answer', 'user_datetime', 'intent')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    if wb:
        return response
    return HttpResponse("No Data Found.")
