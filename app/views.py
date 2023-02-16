from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta
import json
from .forms import CreateUserForm, ChangePasswordForm, ChangeEmailForm, ChangeImageForm
from .models import *
from .mod import *

# Create your views here.
def user_register(request):
    form = CreateUserForm()
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        
        if form.is_valid():
            form.save()  
            messages.success(request,'Rejestracja przebiegła pomyślnie.')
            return redirect('login') 
        
    context = {'form': form}
    return render(request, 'base/register.html', context)


def user_login(request):
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == "" or password == "":
            messages.error(request, 'Proszę wypełnić obydwa pola.')
            return redirect('login')
        
        if  User.objects.filter(username=username).exists():
            user = authenticate(request, username=username, password=password)
        else:
            messages.error(request, 'Użytkownik nie istenieje.')
            return redirect('login')
        
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'Nazwa albo hasło są nieprawidłowe.')
            return redirect('login')
        
    return render(request, 'base/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def user_page(request):
    return render(request, 'base/user_page.html')


@login_required(login_url='login')
def user_change_password(request):
    
    if request.method == 'POST':
        form = ChangePasswordForm(request.user,request.POST)
        
        if form.is_valid():
            form.save()
            username = request.user
            password = request.POST.get('new_password1')
            user = authenticate(request, username=username, password=password)
            login(request,user)  
            messages.success(request,'Zmiana hasła przebiegła pomyślnie')
            return redirect('user_page')
        
    form = ChangePasswordForm(request.user)
    context = {'action':'password',
              'form':form}
    
    return render(request, 'base/user_page.html',context)


@login_required(login_url='login')
def user_change_email(request):

    if request.method =='POST':
        form = ChangeEmailForm(request.user, request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request,'Zmiana emaila przebiegła pomyślnie')
            return redirect('user_page')
        
    form = ChangeEmailForm(request.user)
    old = request.user.email
    context = {'action':'email',
              'form':form,
              'old':old}
    
    return render(request, 'base/user_page.html',context)
   
   
@login_required(login_url='login')
def user_change_image(request):
    form = ChangeImageForm(request.user)
    
    if request.method == 'POST':
        form = ChangeImageForm(request.user, request.POST, request.FILES)
        
        if request.POST.get('save') is not None:
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Udało się zmienić zdjęcie(a)')
                return redirect('user_page')
        else:
            form.reset()
            messages.success(request, 'Zresetowano zdjęcia')
            return redirect('user_page')
        
    context = {'action':'image',
               'form': form}
    
    return render(request, 'base/user_page.html',context) 


@login_required(login_url='login')
def user_delete(request):
    if request.method == 'POST':
        
        request.user.delete()
        messages.success(request,'Konto zostało usunięte')
        return redirect('login')
    
    context = {'action':'delete'}
    
    return render(request, 'base/user_page.html',context)


@login_required(login_url='login')
def home(request):

    nav = request.user.homenavimage
    context = {'image': nav}
    
    return render(request, 'base/home.html', context)


@login_required(login_url='login')
def light(request):
    
    if request.method == 'POST':     
        get_data = json.loads(request.body)
        
        if get_data['action'] == 'change':
            id = get_data['id']
            sensor = Sensor.objects.get(id=id)
            # sensor = request.user.sensor_set.get(id=id)
            # Simulation turn on/off light
            if sensor.name == 'tester':
                light = Light.objects.get(sensor = sensor)
                
                if light.light:
                    light.light = False
                    response = {'response': 0}
                    
                else:
                    light.light = True
                    response = {'response': 1}
                light.save()
                
                return JsonResponse(response)
            # End simulation
            
            return JsonResponse(change_light(get_data['id']))
        
    user = request.user  
    sensors = user.sensor_set.filter(fun = 'light')
    
    context = {
        'sensors': [
            {'id': sensor.id,
             'name': sensor.name,
             'light': sensor.light_set.get().light
             } for sensor in sensors
        ]
    }
    
    return render(request,'base/light.html',context)


@login_required(login_url='login')
def chart(request):
    user_id = request.user.id
    list_place = Sensor.objects.filter(user_id = user_id).filter(fun = 'temp')
    
    if len(list_place) == 0:
         return render(request,'base/chart.html')
    
    data_from = datetime.now().date() - timedelta(days=6)
    data_to = str(datetime.now())
    
    if request.method == 'POST':
        
        if request.POST["data-from"] and request.POST["data-to"]:
            
            data_from = request.POST["data-from"]
            data_to = request.POST["data-to"]
            format = '%Y-%m-%d'
            data_to = str(datetime.strptime(data_to[:19], format) + timedelta(days=1))
  
        place = request.POST["list"]        
        context = data_for_chart(data_from, data_to, place, user_id)
        context['list_place'] = list_place
        
        return render(request,'base/chart.html',context)
    
    place = list_place[0]
    context = data_for_chart(data_from, data_to, place, user_id)
    context['list_place'] = list_place
    
    return render(request,'base/chart.html', context)


@login_required(login_url='login')
def sensor(request):
    user_id = request.user.id
    
    match request.method:
        case 'POST':
            get_data = json.loads(request.body)
            
            # Simulation adding sensors
            if get_data['name'] == 'tester':
                EXCLUDED_SENSORS = ['temp', 'rfid', 'button', 'lamp', 'uid']
                
                if get_data['fun'] in EXCLUDED_SENSORS:
                    return JsonResponse({'response': 'Wybacz akurat tego czujnika nie można dodać w wersji testowej'})
                    
                sensor = Sensor.objects.create(name=get_data['name'],
                                                ip='111.111.111.111',
                                                port=1234, fun=get_data['fun'], 
                                                user_id=user_id)
                return JsonResponse({'response': 'Udało sie dodać czujnik', 'id': sensor.id})
            # End simulation
            
            elif get_data['action'] == 'add' and get_data['fun'] == 'uid' :
                return JsonResponse(add_uid(get_data))
            else:
                return JsonResponse(add_sensor(get_data,user_id))
            
        case 'DELETE':
            get_data = json.loads(request.body)
            return JsonResponse(delete_sensor(get_data))

        case 'GET':
            
            sensors = request.user.sensor_set.filter(user = request.user)
                    
            context = {
                        'sensors': [
                            {
                            'fun':sensor.fun,
                            'name':sensor.name,
                            'id':sensor.id,
                            'cards':[
                                {'id': card.id,'name': card.name} for card in sensor.card_set.all()
                                ] if sensor.fun == 'rfid' else ""
                            } for sensor in sensors]
                        }
    return render(request, 'base/sensor.html',context)


@login_required(login_url='login')
def stairs(request):

    if request.method == 'POST':
        get_data = json.loads(request.body)
        
        sensor = request.user.sensor_set.get(pk = get_data['id'])
        stairs = sensor.stairs
        
        match get_data['action']:
            case 'set-lightingTime':
                
                stairs.lightTime = int(get_data['lightingTime'])
                message ='te'+str(get_data['lightingTime'])
                
            case 'set-brightness':
                
                stairs.brightness = int(get_data['brightness'])
                message = 'bs'+str(get_data['brightness'])
                
            case 'set-step':
                
                stairs.steps = int(get_data['step'])
                message = 'sp'+str(get_data['step'])
                
            case 'change-stairs':
                
                if stairs.mode:
                    stairs.mode = False
                    message = 'OFF'
                else:    
                    stairs.mode = True
                    message = 'ON'
                    
        # Control simulation 
        if sensor.name == 'tester':
            stairs.save()
            return JsonResponse({'success': True})
        # End simulation
        
        if send_data(message,sensor.ip,sensor.port):
            stairs.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})
        
    sensors = request.user.sensor_set.filter(fun = 'stairs')
    context= {
        "sensors": sensors,
    }
    return render(request,'base/stairs.html',context)


@login_required(login_url='login')
def aquarium(request):
    if request.method == "POST":
        get_data = json.loads(request.body)
        sensor = request.user.sensor_set.get(pk = get_data['id'])
        aqua = sensor.aqua
        message = ""
        response = {}
        
        match get_data['action']:
            case 'changeRGB':
                message = 'r'+str(get_data['r'])+'g'+str(get_data['g'])+'b'+str(get_data['b']) 
                aqua.color = message        
                    
            case 'changeLedTime':
                aqua.led_start = get_data['ledStart']
                aqua.led_stop = get_data['ledStop']    
                        
            case 'changeFluoLampTime':
                aqua.fluo_start = get_data['fluoLampStart']
                aqua.fluo_stop = get_data['fluoLampStop']

            case 'changeMode':
                aqua.mode = get_data['mode']
                if get_data['mode']:
                    response ={
                        'fluo': aqua.fluo_mode,
                        'led': aqua.led_mode
                    }
                    aqua.save()
                    return JsonResponse(response)
                else:
                    aqua.save()
                    
            case 'changeFluoLampState':
                if get_data['value']:
                    message = 's1'
                else:
                    message = 's0'
                aqua.fluo_mode=get_data['value']
                
            case 'changeLedState': 
                if get_data['value']:
                    message = 'r1'
                else:
                    message = 'r0'
                aqua.led_mode=get_data['value']          
            
        if message:
            
            # Control simulation 
            if sensor.name == 'tester':
                response = {'success': True,
                            'message':'Udało się zmienić ustawienia'}
                aqua.save()
                return JsonResponse(response)  
            # End simulation
                
            if send_data(message, sensor.ip, sensor.port): 
                response = {'message':'Udało się zmienić ustawienia'}
                aqua.save()   
            else:
                response= {'message':'Brak komunikacji z akwarium'}
        else:
            
             # Control simulation 
            if sensor.name == 'tester':
                response = {'message':'Udało się zmienić ustawienia'}
                aqua.save()
                return JsonResponse(response)  
            # End simulation
            
            if check_aqua(sensor,aqua):
                response = {'message':'Udało się zmienić ustawienia'}
                aqua.save()   
            else:
                response = {'message':'Brak komunikacji z akwarium'}
                
        return JsonResponse(response)

    aquas = request.user.sensor_set.filter(fun = 'aqua')
    context = {
            'aquas':aquas
    }
    return render(request,'base/aquarium.html',context)


@login_required(login_url='login')
def sunblind(request):
    
    if request.method == 'POST':
        get_data = json.loads(request.body)
        sensor = request.user.sensor_set.get(pk = get_data['id'])
        message = 'set' + str(get_data['value'])
        
        # Simulation sunblind
        if sensor.name == 'tester':
            sunblind = sensor.sunblind
            sunblind.value = get_data['value']
            sunblind.save()
            return JsonResponse({'success': 1})
        # End simulation
        
        # Sending message to microcontroller and waiting on response
        if send_data(message,sensor.ip,sensor.port):
            sunblind = sensor.sunblind
            sunblind.value = get_data['value']
            sunblind.save()  
            return JsonResponse({'success': 1})
        else:
            return JsonResponse({'message': 'Brak komunikacji'})

    # Getting all user sensor where function is sunblind
    sensors = request.user.sensor_set.filter(fun = 'sunblind')
    
    context = {
                'sensors': [{
                    'id':sensor.id,
                    'name':sensor.name,
                    'value':sensor.sunblind.value
                    } for sensor in sensors]
                    }
    return render(request,'base/sunblind.html', context)


@login_required(login_url='login')
def calibration(request, pk):
    
    sensor = request.user.sensor_set.get(id=pk)
    if request.method == 'POST':
        
        # Sending 'up', 'down' or 'stop' message to microcontroller
        get_data = json.loads(request.body)
        send_data(get_data['action'], sensor.ip, sensor.port)
        
        # Ending calibration, set value to 100 and save in database
        if get_data['action'] == 'end':
            sunblind = sensor.sunblind
            sunblind.value = 100
            sunblind.save()
        
    elif request.method == 'GET':
        # Sending 'calibration' message to microcontroller 
        send_data('calibration', sensor.ip, sensor.port)

    return render(request,'base/calibration.html')


@login_required(login_url='login')
def rpl(request):
    if request.method == 'POST':
        get_data = json.loads(request.body)
        
        if get_data['action'] == 'get':
            lamp = request.user.sensor_set.get(pk = get_data['id'])
            rfids = Rfid.objects.filter(lamp = lamp.ip)
            buttons = Button.objects.filter(lamp = lamp.ip)
            
            rfid = [r.sensor_id for r in rfids ]
            btn = [b.sensor_id for b in buttons]
   
            respond = {'rfid': rfid,
                       'btn': btn}
            
            return JsonResponse(respond)
        
        elif get_data['action'] == 'connect':
            lamp = request.user.sensor_set.get(pk = get_data['lamp'])   
            rfids = Rfid.objects.filter(lamp = lamp.ip)
            btns = Button.objects.filter(lamp = lamp.ip)
            
            btn_connected = set([b.sensor_id for b in btns])
            btn_connect = set([int(i) for i in get_data['btns']])
            
            btn_add = btn_connect - btn_connected
            btn_remove = btn_connected - btn_connect

            rfid_connected = set([r.sensor_id for r in rfids])
            rfid_connect = set([int(i) for i in get_data['rfids']])
            
            rfid_add = rfid_connect - rfid_connected
            rfid_remove =rfid_connected - rfid_connect
            
            for id in rfid_add:
                rfid = Rfid.objects.get(sensor_id = id)
                rfid.lamp = lamp.ip
                rfid.save()
                
            for id in rfid_remove:
                rfid = Rfid.objects.get(sensor_id = id)
                rfid.lamp = ""
                rfid.save()
                
            for id in btn_add:
                btn = Button.objects.get(sensor_id = id)
                btn.lamp = lamp.ip
                btn.save()
                
            for id in btn_remove:
                btn = Button.objects.get(sensor_id = id)
                btn.lamp = ""
                btn.save()
            
            message = {'message':'Połączono'}
            return JsonResponse(message)
                                
    rfids = request.user.sensor_set.filter(fun = 'rfid')
    lamps = request.user.sensor_set.filter(fun = 'lamp')
    buttons = request.user.sensor_set.filter(fun = 'btn')
    
    context= {'rfids':[{
                  'id':rfid.id,
                  'name':rfid.name} for rfid in rfids],
              'lamps':[{
                  'id':lamp.id,
                  'name':lamp.name} for lamp in lamps],
              'buttons':[{
                  'id':button.id,
                  'name':button.name} for button in buttons]}
    
    return render(request,'base/rpl.html',context)