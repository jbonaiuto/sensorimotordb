import csv
from datetime import datetime
from decimal import Decimal
from shutil import copyfile
import django
from django.contrib.auth.models import User
from django.db import connections
from haystack.management.commands import rebuild_index
from neo import io, os
import scipy.io
import numpy as np
from glob import glob
import pandas as pd
from django.db.models import Q, Max
from sensorimotordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, \
    Species, GraspPerformanceCondition, Condition, UnitRecording, ConditionVideoEvent, Penetration, Subject, Array, \
    Nomenclature
from uscbp import settings

def remove_all(db='default'):
    for condition in Condition.objects.using(db).all():
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,'video','condition_%d.mp4' % condition.id)):
            os.remove(os.path.join(settings.MEDIA_ROOT,'video','condition_%d.mp4' % condition.id))
    cursor=connections[db].cursor()
    cursor.execute('DELETE FROM %s.sensorimotordb_experimentexportrequest WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_event WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_unitrecording WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_recordingtrial WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_penetration WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_array WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_unit WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspobservationcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspperformancecondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_conditionvideoevent WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_condition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_subject WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    for exp in Experiment.objects.using(db).all():
        cursor.execute('DELETE FROM %s.sensorimotordb_experiment WHERE id=%d' % (settings.DATABASES[db]['NAME'],exp.id))
    cursor.close()

def import_kraskov_data(mat_file, video_dir, db='default'):
    exps={}

    sensorimotordb_video_dir=os.path.join(settings.MEDIA_ROOT,'video')
    if not os.path.exists(settings.MEDIA_ROOT):
        os.mkdir(settings.MEDIA_ROOT)
    if not os.path.exists(sensorimotordb_video_dir):
        os.mkdir(sensorimotordb_video_dir)

    collator=User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='akraskov').count():
        collator=User.objects.using(db).get(username='akraskov')

    exps['m1_ptn']=Experiment()
    exps['m1_ptn'].collator=collator
    exps['m1_ptn'].last_modified_by=collator
    exps['m1_ptn'].title='M1 PTN - Observation/Execution of Grasps'
    exps['m1_ptn'].brief_description='Recording of M1 pyramidal tract neurons (PTNs) while monkeys observed or performed object-directed grasps'
    exps['m1_ptn'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    exps['m1_ptn'].save(using=db)
    
    exps['m1_uid']=Experiment()
    exps['m1_uid'].collator=collator
    exps['m1_uid'].last_modified_by=collator
    exps['m1_uid'].title='M1 Observation/Execution of Grasps'
    exps['m1_uid'].brief_description='Recording of unidentified M1 neurons while monkeys observed or performed object-directed grasps'
    exps['m1_uid'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    exps['m1_uid'].save(using=db)
    
    exps['f5_ptn']=Experiment()
    exps['f5_ptn'].collator=collator
    exps['f5_ptn'].last_modified_by=collator
    exps['f5_ptn'].title='F5 PTN - Observation/Execution of Grasps'
    exps['f5_ptn'].brief_description='Recording of F5 pyramidal tract neurons (PTNs) while monkeys observed or performed object-directed grasps'
    exps['f5_ptn'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    exps['f5_ptn'].save(using=db)
    
    exps['f5_uid']=Experiment()
    exps['f5_uid'].collator=collator
    exps['f5_uid'].last_modified_by=collator
    exps['f5_uid'].title='F5 Observation/Execution of Grasps'
    exps['f5_uid'].brief_description='Recording of unidentified F5 neurons while monkeys observed or performed object-directed grasps'
    exps['f5_uid'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    exps['f5_uid'].save(using=db)
    
    exp_conditions={}
    for exp_id, exp in exps.iteritems():
        if not exp_id in exp_conditions:
            exp_conditions[exp_id]={}

        exp_conditions[exp_id]['obs_ring']=GraspObservationCondition()
        exp_conditions[exp_id]['obs_ring'].experiment=exp
        exp_conditions[exp_id]['obs_ring'].name='Observe ring hook grasp'
        exp_conditions[exp_id]['obs_ring'].description='Monkeys observed the human experimenter grasping a ring using a hook grip with just the index finger'
        exp_conditions[exp_id]['obs_ring'].type='grasp_observe'
        exp_conditions[exp_id]['obs_ring'].object='ring'
        exp_conditions[exp_id]['obs_ring'].object_distance=63.8
        exp_conditions[exp_id]['obs_ring'].whole_body_visible=True
        exp_conditions[exp_id]['obs_ring'].grasp='hook'
        exp_conditions[exp_id]['obs_ring'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        exp_conditions[exp_id]['obs_ring'].demonstration_type='live'
        exp_conditions[exp_id]['obs_ring'].viewing_angle=180.0
        exp_conditions[exp_id]['obs_ring'].save(using=db)

        exp_conditions[exp_id]['mov_ring']=GraspPerformanceCondition()
        exp_conditions[exp_id]['mov_ring'].experiment=exp
        exp_conditions[exp_id]['mov_ring'].name='Execute ring hook grasp'
        exp_conditions[exp_id]['mov_ring'].description='Monkeys grasped a ring using a hook grip with just the index finger'
        exp_conditions[exp_id]['mov_ring'].type='grasp_perform'
        exp_conditions[exp_id]['mov_ring'].object='ring'
        exp_conditions[exp_id]['mov_ring'].object_distance=34.3
        exp_conditions[exp_id]['mov_ring'].grasp='hook'
        exp_conditions[exp_id]['mov_ring'].hand_visible=True
        exp_conditions[exp_id]['mov_ring'].object_visible=True
        exp_conditions[exp_id]['mov_ring'].save(using=db)

        copyfile(os.path.join(video_dir,'ring.mp4'),os.path.join(sensorimotordb_video_dir,'condition_%d.mp4' % exp_conditions[exp_id]['mov_ring'].id))

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=0.266
        event.code='start'
        event.description='trial start'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=1.134
        event.code='go'
        event.description='go signal'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=1.401
        event.code='mo'
        event.description='movement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=1.668
        event.code='do'
        event.description='displacement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=1.935
        event.code='ho'
        event.description='hold onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_ring']
        event.time=2.735
        event.code='hoff'
        event.description='hold offset'
        event.save()



        exp_conditions[exp_id]['obs_sphere']=GraspObservationCondition()
        exp_conditions[exp_id]['obs_sphere'].experiment=exp
        exp_conditions[exp_id]['obs_sphere'].name='Observe sphere whole hand grasp'
        exp_conditions[exp_id]['obs_sphere'].description='Monkeys observed the human experimenter grasping a sphere using the whole hand by opposing all the fingers to the palm'
        exp_conditions[exp_id]['obs_sphere'].type='grasp_observe'
        exp_conditions[exp_id]['obs_sphere'].object='sphere'
        exp_conditions[exp_id]['obs_sphere'].grasp='whole hand'
        exp_conditions[exp_id]['obs_sphere'].object_distance=63.8
        exp_conditions[exp_id]['obs_sphere'].whole_body_visible=True
        exp_conditions[exp_id]['obs_sphere'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        exp_conditions[exp_id]['obs_sphere'].demonstration_type='live'
        exp_conditions[exp_id]['obs_sphere'].viewing_angle=180.0
        exp_conditions[exp_id]['obs_sphere'].save(using=db)

        exp_conditions[exp_id]['mov_sphere']=GraspPerformanceCondition()
        exp_conditions[exp_id]['mov_sphere'].experiment=exp
        exp_conditions[exp_id]['mov_sphere'].name='Execute sphere whole hand'
        exp_conditions[exp_id]['mov_sphere'].description='Monkeys grasped a sphere using the whole hand by opposing all the fingers to the palm'
        exp_conditions[exp_id]['mov_sphere'].type='grasp_perform'
        exp_conditions[exp_id]['mov_sphere'].object='sphere'
        exp_conditions[exp_id]['mov_sphere'].object_distance=34.3
        exp_conditions[exp_id]['mov_sphere'].grasp='whole hand'
        exp_conditions[exp_id]['mov_sphere'].hand_visible=True
        exp_conditions[exp_id]['mov_sphere'].object_visible=True
        exp_conditions[exp_id]['mov_sphere'].save(using=db)

        copyfile(os.path.join(video_dir,'sphere.mp4'),os.path.join(sensorimotordb_video_dir,'condition_%d.mp4' % exp_conditions[exp_id]['mov_sphere'].id))

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=0.313
        event.code='start'
        event.description='trial start'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=1.180
        event.code='go'
        event.description='go signal'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=1.380
        event.code='mo'
        event.description='movement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=1.581
        event.code='do'
        event.description='displacement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=1.714
        event.code='ho'
        event.description='hold onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=2.848
        event.code='hoff'
        event.description='hold offset'
        event.save()

        exp_conditions[exp_id]['obs_trapezoid']=GraspObservationCondition()
        exp_conditions[exp_id]['obs_trapezoid'].experiment=exp
        exp_conditions[exp_id]['obs_trapezoid'].name='Observe trapezoid precision grasp'
        exp_conditions[exp_id]['obs_trapezoid'].description='Monkeys observed the human experimenter grasping a trapezoid using a precision grasp with the thumb and forefinger'
        exp_conditions[exp_id]['obs_trapezoid'].type='grasp_observe'
        exp_conditions[exp_id]['obs_trapezoid'].object='trapezoid'
        exp_conditions[exp_id]['obs_trapezoid'].grasp='precision'
        exp_conditions[exp_id]['obs_trapezoid'].object_distance=63.8
        exp_conditions[exp_id]['obs_trapezoid'].whole_body_visible=True
        exp_conditions[exp_id]['obs_trapezoid'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        exp_conditions[exp_id]['obs_trapezoid'].demonstration_type='live'
        exp_conditions[exp_id]['obs_trapezoid'].viewing_angle=180.0
        exp_conditions[exp_id]['obs_trapezoid'].save(using=db)

        exp_conditions[exp_id]['mov_trapezoid']=GraspPerformanceCondition()
        exp_conditions[exp_id]['mov_trapezoid'].experiment=exp
        exp_conditions[exp_id]['mov_trapezoid'].name='Execute trapezoid precision grasp'
        exp_conditions[exp_id]['mov_trapezoid'].description='Monkeys grasped a trapezoid using a precision grasp with the thumb and forefinger'
        exp_conditions[exp_id]['mov_trapezoid'].type='grasp_perform'
        exp_conditions[exp_id]['mov_trapezoid'].object='trapezoid'
        exp_conditions[exp_id]['mov_trapezoid'].object_distance=34.3
        exp_conditions[exp_id]['mov_trapezoid'].grasp='precision'
        exp_conditions[exp_id]['mov_trapezoid'].hand_visible=True
        exp_conditions[exp_id]['mov_trapezoid'].object_visible=True
        exp_conditions[exp_id]['mov_trapezoid'].save(using=db)

        copyfile(os.path.join(video_dir,'trapezoid.mp4'),os.path.join(sensorimotordb_video_dir,'condition_%d.mp4' % exp_conditions[exp_id]['mov_trapezoid'].id))

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_trapezoid']
        event.time=0.107
        event.code='start'
        event.description='trial start'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_trapezoid']
        event.time=1.308
        event.code='go'
        event.description='go signal'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_trapezoid']
        event.time=1.508
        event.code='mo'
        event.description='movement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_trapezoid']
        event.time=1.775
        event.code='do'
        event.description='displacement onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_trapezoid']
        event.time=1.842
        event.code='ho'
        event.description='hold onset'
        event.save()

        event=ConditionVideoEvent()
        event.condition=exp_conditions[exp_id]['mov_sphere']
        event.time=3.176
        event.code='hoff'
        event.description='hold offset'
        event.save()

    # create event types (if not already exist)
    # load file
    mat_file=scipy.io.loadmat(mat_file)

    trial_numbers={}

    for i in range(len(mat_file['U'][0])):
        print('importing unit %d' % i)
        area_idx=-1
        unittype_idx=-1
        index_idx=-1
        events_idx=-1

        # get indices of area, unit type, index, and events
        for idx,(dtype,o) in enumerate(mat_file['U'][0][i].dtype.descr):
            if dtype=='area':
                area_idx=idx
            elif dtype=='unittype':
                unittype_idx=idx
            elif dtype=='index':
                index_idx=idx
            elif dtype=='events':
                events_idx=idx

        # create unit
        unit=Unit()
        area=mat_file['U'][0][i][area_idx][0]
        region=BrainRegion.objects.using(db).filter(Q(Q(name=area) | Q(abbreviation=area)))
        unit.area=region[0]
        unit.type=mat_file['U'][0][i][unittype_idx][0]
        unit.save(using=db)

        if not unit.id in trial_numbers:
            trial_numbers[unit.id]={}

        exp_id=''
        if area=='M1':
            if unit.type=='PTN':
                exp_id='m1_ptn'
            elif unit.type=='UID':
                exp_id='m1_uid'
            else:
                print('SED not found: %s, %s' % (area,unit.type))
        elif area=='F5':
            if unit.type=='PTN':
                exp_id='f5_ptn'
            elif unit.type=='UID':
                exp_id='f5_uid'
            else:
                print('SED not found: %s, %s' % (area,unit.type))
        else:
            print('SED not found: %s, %s' % (area,unit.type))

        index=mat_file['U'][0][i][index_idx]
        events=mat_file['U'][0][i][events_idx]

        trialtype_idx=-1
        object_idx=-1
        trial_start_idx=-1
        go_idx=-1
        mo_idx=-1
        do_idx=-1
        ho_idx=-1
        hoff_idx=-1
        trial_end_idx=-1
        for idx,(dtype,o) in enumerate(events[0].dtype.descr):
            if dtype=='trialtype':
                trialtype_idx=idx
            elif dtype=='object':
                object_idx=idx
            elif dtype=='TrialStart':
                trial_start_idx=idx
            elif dtype=='Go':
                go_idx=idx
            elif dtype=='MO':
                mo_idx=idx
            elif dtype=='DO':
                do_idx=idx
            elif dtype=='HO':
                ho_idx=idx
            elif dtype=='HOff':
                hoff_idx=idx
            elif dtype=='TrialEnd':
                trial_end_idx=idx

        trial_types=events[0][0][trialtype_idx][0]
        objects=events[0][0][object_idx][0]
        trial_start_times=events[0][0][trial_start_idx][0]
        go_events=events[0][0][go_idx][0]
        mo_events=events[0][0][mo_idx][0]
        do_events=events[0][0][do_idx][0]
        ho_events=events[0][0][ho_idx][0]
        hoff_events=events[0][0][hoff_idx][0]
        trial_end_times=events[0][0][trial_end_idx][0]

        # iterate through trials
        for j in range(len(trial_types)):
            # create trial
            trial=RecordingTrial()
            if trial_types[j]=='h':
                if objects[j]==1:
                    trial.condition=exp_conditions[exp_id]['obs_ring']
                elif objects[j]==2:
                    trial.condition=exp_conditions[exp_id]['obs_sphere']
                elif objects[j]==4:
                    trial.condition=exp_conditions[exp_id]['obs_trapezoid']
            elif trial_types[j]=='m':
                if objects[j]==1:
                    trial.condition=exp_conditions[exp_id]['mov_ring']
                elif objects[j]==2:
                    trial.condition=exp_conditions[exp_id]['mov_sphere']
                elif objects[j]==4:
                    trial.condition=exp_conditions[exp_id]['mov_trapezoid']
            if not trial.condition.id in trial_numbers[unit.id]:
                trial_numbers[unit.id][trial.condition.id]=0
            trial_numbers[unit.id][trial.condition.id]+=1
            trial.trial_number=trial_numbers[unit.id][trial.condition.id]
            trial.start_time=trial_start_times[j]
            trial.end_time=trial_end_times[j]
            trial.save(using=db)

            next_trial_start_time=None
            if j<len(trial_types)-1:
                next_trial_start_time=trial_start_times[j+1]

            previous_trial=None
            if trial_numbers[unit.id][trial.condition.id]>1:
                previous_trial=RecordingTrial.objects.using(db).get(condition=trial.condition,
                    unit_recordings__unit=unit, trial_number=trial_numbers[unit.id][trial.condition.id]-1)

            unit_recording=UnitRecording(unit=unit, trial=trial)
            # load spikes
            spike_times=[]
            for k in range(len(index)):
                if previous_trial is None:
                    if index[k,0]>=trial.start_time-1.0:
                        if next_trial_start_time is None:
                            if index[k,0]<trial.end_time+1.0:
                                spike_times.append(index[k,0])
                        elif index[k,0]<trial.end_time+1.0 and index[k,0]<next_trial_start_time:
                            spike_times.append(index[k,0])
                elif index[k,0]>=trial.start_time-1.0 and index[k,0]>=previous_trial.end_time:
                    if next_trial_start_time is None:
                        if index[k,0]<trial.end_time+1.0:
                            spike_times.append(index[k,0])
                    elif index[k,0]<trial.end_time+1.0 and index[k,0]<next_trial_start_time:
                        spike_times.append(index[k,0])

            unit_recording.spike_times=','.join([str(x) for x in sorted(spike_times)])
            unit_recording.save(using=db)

            # create trial events
            go_event=Event(name='go', description='go signal', trial=trial, time=go_events[j])
            go_event.save(using=db)

            mo_event=Event(name='mo', description='movement onset', trial=trial, time=mo_events[j])
            mo_event.save(using=db)

            do_event=Event(name='do', description='object displacement onset', trial=trial, time=do_events[j])
            do_event.save(using=db)

            ho_event=Event(name='ho', description='stable hold onset', trial=trial, time=ho_events[j])
            ho_event.save(using=db)

            hoff_event=Event(name='hoff', description='hold offset', trial=trial, time=hoff_events[j])
            hoff_event.save(using=db)


def import_bonini_data(nex_files, db='default'):
    collator=User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='lbonini').count():
        collator=User.objects.using(db).get(username='lbonini')

    event_map={
        'ev_01_LightON_visualCOR_RNG':('lon','light on'),
        'ev_02_LightON_motorCORc1_RNG':('lon','light on'),
        'ev_03_Pull_CORc1_RNG': ('do','object displacement onset'),
        'ev_04_Pull_CORc2_RNG': ('do','object displacement onset'),
        'ev_05_LightON_visualCOR_SML': ('lon','light on'),
        'ev_06_LightON_motorCORc1_SML': ('lon','light on'),
        'ev_07_Pull_CORc1_SML': ('do','object displacement onset'),
        'ev_08_Pull_CORc2_SML': ('do','object displacement onset'),
        'ev_09_LightON_visualCOR_BIG': ('lon','light on'),
        'ev_10_LightON_motorCORc1_BIG': ('lon','light on'),
        'ev_11_Pull_CORc1_BIG': ('do','object displacement onset'),
        'ev_12_Pull_CORc2_BIG': ('do','object displacement onset'),
        'LightON_motorCORc2_RNG': ('lon','light on'),
        'LightON_motorCORc2_SML': ('lon','light on'),
        'LightON_motorCORc2_BIG': ('lon','light on'),
        # Object contact events are not reliable
        #        'EVT02': ('co','object contact'),
        #        'EVT03': ('co','object contact'),
        #        'EVT04': ('co','object contact'),
        'EVT07': ('rew','reward onset'),
        'EVT09': ('fix','fixation onset'),
        'EVT17': ('mo','movement onset'),
        'EVT23': ('loff','light off'),
        'EVT28': ('mo','movement onset'),
        }
    exp_title='F5 mirror neuron depth recording - Observation/Execution of Grasps'
    if Experiment.objects.using(db).filter(title=exp_title).count():
        exp=Experiment.objects.using(db).filter(title=exp_title)[0]
    else:
        exp=Experiment()
        exp.collator=collator
        exp.last_modified_by=collator
        exp.title=exp_title
        exp.brief_description='Recording of unidentified F5 neurons while monkeys observed or performed object-directed grasps'
        exp.subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
        exp.save(using=db)
    print('importing experiment %d' % exp.id)

    obs_conditions={}
    mov_conditions={}
    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe ring hook grasp').count():
        obs_conditions['ring_go_light']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe ring hook grasp')[0]
    else:
        obs_conditions['ring_go_light']=GraspObservationCondition()
        obs_conditions['ring_go_light'].experiment=exp
        obs_conditions['ring_go_light'].name='Observe ring hook grasp'
        obs_conditions['ring_go_light'].description='Monkeys observed the human experimenter grasping a ring using a '\
                                                    'hook grip with just the index finger. The fixation point was '\
                                                    'presented and the monkey was required to start fixating it '\
                                                    'within 1.2 s. Fixation onset determined the presentation of a '\
                                                    'cue sound (a pure high tone constituted by a 1200 Hz sine '\
                                                    'wave). After 0.8 s, the upper sector of the box was illuminated '\
                                                    'and the experimenter\'s hand and a ring became visible at a '\
                                                    '90 degree angle. Then, after a variable time lag (0.8-1.2 s), '\
                                                    'the sound ceased (go signal) and the experimenter reached, '\
                                                    'grasped, and pulled the object within 1.2 s. Then the '\
                                                    'experimenter held the object steadily for at least 0.8 s. If '\
                                                    'the monkey did not break fixation, a juice reward was automatically '\
                                                    'delivered.'
        obs_conditions['ring_go_light'].type='grasp_observe'
        obs_conditions['ring_go_light'].object='ring'
        obs_conditions['ring_go_light'].grasp='hook'
        # What is the distance?
        obs_conditions['ring_go_light'].object_distance=63.8
        obs_conditions['ring_go_light'].whole_body_visible=False
        obs_conditions['ring_go_light'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['ring_go_light'].demonstration_type='live'
        obs_conditions['ring_go_light'].viewing_angle=90.0
        obs_conditions['ring_go_light'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe ring - nogo').count():
        obs_conditions['ring_nogo']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe ring - nogo')[0]
    else:
        obs_conditions['ring_nogo']=GraspObservationCondition()
        obs_conditions['ring_nogo'].experiment=exp
        obs_conditions['ring_nogo'].name='Observe ring hook grasp - nogo'
        obs_conditions['ring_nogo'].description='Monkeys observed the human experimenter\'s hand resting next to a '\
                                                'ring. The fixation point was presented and the monkey was required '\
                                                'to start fixating it within 1.2 s. Fixation onset determined the '\
                                                'presentation of a cue sound (a pure low tone constituted by a '\
                                                '300 Hz sine wave). After 0.8 s, the upper sector of the box was '\
                                                'illuminated and the experimenter\'s hand and a ring became visible. '\
                                                'Then, after a variable time lag (0.8-1.2 s), the sound ceased and '\
                                                'the monkey had to continue to maintain fixation for 1.2 s to '\
                                                'receive a drop of juice as a reward.'
        obs_conditions['ring_nogo'].type='grasp_observe'
        obs_conditions['ring_nogo'].object='ring'
        obs_conditions['ring_nogo'].grasp=''
        # What is the distance?
        obs_conditions['ring_nogo'].object_distance=63.8
        obs_conditions['ring_nogo'].whole_body_visible=False
        obs_conditions['ring_nogo'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['ring_nogo'].demonstration_type='live'
        obs_conditions['ring_nogo'].viewing_angle=90.0
        obs_conditions['ring_nogo'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute ring hook grasp').count():
        mov_conditions['ring_go_light']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute ring hook grasp')[0]
    else:
        mov_conditions['ring_go_light']=GraspPerformanceCondition()
        mov_conditions['ring_go_light'].experiment=exp
        mov_conditions['ring_go_light'].name='Execute ring hook grasp'
        mov_conditions['ring_go_light'].description='Monkeys grasped a ring using a hook grip with just the index finger. '\
                                                    'The fixation point was presented and the monkey was required to '\
                                                    'start fixating it within 1.2 s. Fixation onset determined the '\
                                                    'presentation of a cue sound (a pure high tone constituted by a 1200 '\
                                                    'Hz sine wave), which instructed the monkey to grasp the subsequently '\
                                                    'presented object. After 0.8 s, the lower sector of the box was '\
                                                    'illuminated and a ring became visible. Then, after a variable '\
                                                    'time lag (0.8-1.2 s), the sound ceased (go signal) and the monkey '\
                                                    'had to reach, grasp, and pull the object within 1.2 s. Then it had '\
                                                    'to hold the object steadily for at least 0.8 s. If the task was '\
                                                    'performed correctly without breaking fixation, a juice reward was '\
                                                    'automatically delivered.'
        mov_conditions['ring_go_light'].type='grasp_perform'
        mov_conditions['ring_go_light'].object='ring'
        # What is the distance?
        mov_conditions['ring_go_light'].object_distance=34.3
        mov_conditions['ring_go_light'].grasp='hook'
        mov_conditions['ring_go_light'].hand_visible=True
        mov_conditions['ring_go_light'].object_visible=True
        mov_conditions['ring_go_light'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute ring hook grasp in the dark').count():
        mov_conditions['ring_go_dark']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute ring hook grasp in the dark - go')[0]
    else:
        mov_conditions['ring_go_dark']=GraspPerformanceCondition()
        mov_conditions['ring_go_dark'].experiment=exp
        mov_conditions['ring_go_dark'].name='Execute ring hook grasp in the dark'
        mov_conditions['ring_go_dark'].description='Monkeys grasped a ring in the dark using a hook grip with just the '\
                                                   'index finger. The fixation point was presented and the monkey was '\
                                                   'required to start fixating it within 1.2 s. Fixation onset '\
                                                   'determined the presentation of a cue sound (a pure high tone '\
                                                   'constituted by a 1200 Hz sine wave), which instructed the monkey '\
                                                   'to grasp the subsequently presented object. After 0.8 s, the lower '\
                                                   'sector of the box was illuminated and a ring became visible. Then, '\
                                                   'after a variable time lag (0.8-1.2 s), the sound ceased (go '\
                                                   'signal) and the light inside the box was automatically turned off '\
                                                   'and the monkey performed the subsequent motor acts in complete '\
                                                   'darkness. The monkey had to reach, grasp, and pull the object '\
                                                   'within 1.2 s. Then it had to hold the object steadily for at least '\
                                                   '0.8 s. If the task was performed correctly without breaking '\
                                                   'fixation, a juice reward was automatically delivered.'
        mov_conditions['ring_go_dark'].type='grasp_perform'
        mov_conditions['ring_go_dark'].object='ring'
        # What is the distance?
        mov_conditions['ring_go_dark'].object_distance=34.3
        mov_conditions['ring_go_dark'].grasp='hook'
        mov_conditions['ring_go_dark'].hand_visible=False
        mov_conditions['ring_go_dark'].object_visible=False
        mov_conditions['ring_go_dark'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe ring - nogo').count():
        mov_conditions['ring_nogo']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe ring - nogo')[0]
    else:
        mov_conditions['ring_nogo']=GraspPerformanceCondition()
        mov_conditions['ring_nogo'].experiment=exp
        mov_conditions['ring_nogo'].name='Observe ring - nogo'
        mov_conditions['ring_nogo'].description='Monkeys observed a ring. The fixation point was presented and the '\
                                                'monkey was required to start fixating it within 1.2 s. Fixation '\
                                                'onset determined the presentation of a cue sound (a pure low tone '\
                                                'constituted by a 300 Hz sine wave), which was associated with object '\
                                                'fixation trials. After 0.8 s, the lower sector of the box was '\
                                                'illuminated and a ring became visible. Then, after a variable time '\
                                                'lag (0.8-1.2 s), the sound ceased and the monkey had to maintain '\
                                                'fixation for 1.2 s to receive a drop of juice as a reward.'
        mov_conditions['ring_nogo'].type='grasp_perform'
        mov_conditions['ring_nogo'].object='ring'
        # What is the distance?
        mov_conditions['ring_nogo'].object_distance=34.3
        mov_conditions['ring_nogo'].grasp=''
        mov_conditions['ring_nogo'].hand_visible=True
        mov_conditions['ring_nogo'].object_visible=True
        mov_conditions['ring_nogo'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe small cone side grasp').count():
        obs_conditions['small_cone_go_light']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe small cone side grasp')[0]
    else:
        obs_conditions['small_cone_go_light']=GraspObservationCondition()
        obs_conditions['small_cone_go_light'].experiment=exp
        obs_conditions['small_cone_go_light'].name='Observe small cone side grasp'
        obs_conditions['small_cone_go_light'].description='Monkeys observed the human experimenter grasping a small '\
                                                          'cone by opposing the thumb and the lateral surface of the '\
                                                          'index finger. The fixation point was presented and the '\
                                                          'monkey was required to start fixating it within 1.2 s. '\
                                                          'Fixation onset determined the presentation of a cue sound '\
                                                          '(a pure high tone constituted by a 1200 Hz sine wave). '\
                                                          'After 0.8 s, the upper sector of the box was illuminated '\
                                                          'and the experimenter\'s hand and a small cone became '\
                                                          'visible at a 90 degree angle. Then, after a variable time '\
                                                          'lag (0.8-1.2 s), the sound ceased (go signal) and the '\
                                                          'experimenter reached, grasped, and pulled the object '\
                                                          'within 1.2 s. Then the experimenter held the object '\
                                                          'steadily for at least 0.8 s. If the monkey did not break '\
                                                          'fixation, a juice reward was automatically delivered.'
        obs_conditions['small_cone_go_light'].type='grasp_observe'
        obs_conditions['small_cone_go_light'].object='small cone'
        obs_conditions['small_cone_go_light'].grasp='side'
        # What is the distance?
        obs_conditions['small_cone_go_light'].object_distance=63.8
        obs_conditions['small_cone_go_light'].whole_body_visible=False
        obs_conditions['small_cone_go_light'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['small_cone_go_light'].demonstration_type='live'
        obs_conditions['small_cone_go_light'].viewing_angle=90.0
        obs_conditions['small_cone_go_light'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe small cone side grasp - nogo').count():
        obs_conditions['small_cone_nogo']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe small cone - nogo')[0]
    else:
        obs_conditions['small_cone_nogo']=GraspObservationCondition()
        obs_conditions['small_cone_nogo'].experiment=exp
        obs_conditions['small_cone_nogo'].name='Observe small cone - nogo'
        obs_conditions['small_cone_nogo'].description='Monkeys observed the human experimenter\'s hand resting next '\
                                                      'to a small cone. The fixation point was presented and the '\
                                                      'monkey was required to start fixating it within 1.2 s. '\
                                                      'Fixation onset determined the presentation of a cue sound (a '\
                                                      'pure low tone constituted by a 300 Hz sine wave). After '\
                                                      '0.8 s, the upper sector of the box was illuminated and the '\
                                                      'experimenter\'s hand and a small cone became visible. Then, '\
                                                      'after a variable time lag (0.8-1.2 s), the sound ceased and '\
                                                      'the monkey had to continue to maintain fixation for 1.2 s to '\
                                                      'receive a drop of juice as a reward.'
        obs_conditions['small_cone_nogo'].type='grasp_observe'
        obs_conditions['small_cone_nogo'].object='small cone'
        obs_conditions['small_cone_nogo'].grasp=''
        # What is the distance?
        obs_conditions['small_cone_nogo'].object_distance=63.8
        obs_conditions['small_cone_nogo'].whole_body_visible=False
        obs_conditions['small_cone_nogo'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['small_cone_nogo'].demonstration_type='live'
        obs_conditions['small_cone_nogo'].viewing_angle=90.0
        obs_conditions['small_cone_nogo'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute small cone side grasp').count():
        mov_conditions['small_cone_go_light']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute small cone side grasp')[0]
    else:
        mov_conditions['small_cone_go_light']=GraspPerformanceCondition()
        mov_conditions['small_cone_go_light'].experiment=exp
        mov_conditions['small_cone_go_light'].name='Execute small cone side grasp'
        mov_conditions['small_cone_go_light'].description='Monkeys grasped a small cone by opposing the thumb and the '\
                                                          'lateral surface of the index finger. The fixation point was '\
                                                          'presented and the monkey was required to start fixating it '\
                                                          'within 1.2 s. Fixation onset determined the presentation of '\
                                                          'a cue sound (a pure high tone constituted by a 1200 Hz sine '\
                                                          'wave), which instructed the monkey to grasp the '\
                                                          'subsequently presented object. After 0.8 s, the lower '\
                                                          'sector of the box was illuminated and a small cone became '\
                                                          'visible. Then, after a variable time lag (0.8-1.2 s), the '\
                                                          'sound ceased (go signal) and the monkey had to reach, '\
                                                          'grasp, and pull the object within 1.2 s. Then it had to '\
                                                          'hold the object steadily for at least 0.8 s. If the task was '\
                                                          'performed correctly without breaking fixation, a juice reward '\
                                                          'was automatically delivered.'
        mov_conditions['small_cone_go_light'].type='grasp_perform'
        mov_conditions['small_cone_go_light'].object='small cone'
        # What is the distance?
        mov_conditions['small_cone_go_light'].object_distance=34.3
        mov_conditions['small_cone_go_light'].grasp='side'
        mov_conditions['small_cone_go_light'].hand_visible=True
        mov_conditions['small_cone_go_light'].object_visible=True
        mov_conditions['small_cone_go_light'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute small cone side grasp in the dark').count():
        mov_conditions['small_cone_go_dark']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute small cone side grasp in the dark')[0]
    else:
        mov_conditions['small_cone_go_dark']=GraspPerformanceCondition()
        mov_conditions['small_cone_go_dark'].experiment=exp
        mov_conditions['small_cone_go_dark'].name='Execute small cone side grasp in the dark'
        mov_conditions['small_cone_go_dark'].description='Monkeys grasped a small cone in the dark by opposing the thumb '\
                                                         'and the lateral surface of the index finger. The fixation '\
                                                         'point was presented and the monkey was required to start '\
                                                         'fixating it within 1.2 s. Fixation onset determined the '\
                                                         'presentation of a cue sound (a pure high tone constituted by a '\
                                                         '1200 Hz sine wave), which instructed the monkey to grasp the '\
                                                         'subsequently presented object. After 0.8 s, the lower sector '\
                                                         'of the box was illuminated and a small cone became visible. '\
                                                         'Then, after a variable time lag (0.8-1.2 s), the sound ceased '\
                                                         '(go signal) and the light inside the box was automatically '\
                                                         'turned off and the monkey performed the subsequent motor acts '\
                                                         'in complete darkness. The monkey had to reach, grasp, and pull '\
                                                         'the object within 1.2 s. Then it had to hold the object '\
                                                         'steadily for at least 0.8 s. If the task was performed '\
                                                         'correctly without breaking fixation, a juice reward was '\
                                                         'automatically delivered.'
        mov_conditions['small_cone_go_dark'].type='grasp_perform'
        mov_conditions['small_cone_go_dark'].object='small cone'
        # What is the distance?
        mov_conditions['small_cone_go_dark'].object_distance=34.3
        mov_conditions['small_cone_go_dark'].grasp='side'
        mov_conditions['small_cone_go_dark'].hand_visible=False
        mov_conditions['small_cone_go_dark'].object_visible=False
        mov_conditions['small_cone_go_dark'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe small cone - nogo').count():
        mov_conditions['small_cone_nogo']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe small cone - nogo')[0]
    else:
        mov_conditions['small_cone_nogo']=GraspPerformanceCondition()
        mov_conditions['small_cone_nogo'].experiment=exp
        mov_conditions['small_cone_nogo'].name='Observe small cone - nogo'
        mov_conditions['small_cone_nogo'].description='Monkeys observed a small cone. The fixation point was '\
                                                      'presented and the monkey was required to start fixating it '\
                                                      'within 1.2 s. Fixation onset determined the presentation '\
                                                      'of a cue sound (a pure low tone constituted by a 300 Hz '\
                                                      'sine wave), which was associated with object fixation trials. '\
                                                      'After 0.8 s, the lower sector of the box was illuminated and '\
                                                      'a small cone became visible. Then, after a variable time lag '\
                                                      '(0.8-1.2 s), the sound ceased and the monkey had to maintain '\
                                                      'fixation for 1.2 s to receive a drop of juice as a reward.'
        mov_conditions['small_cone_nogo'].type='grasp_perform'
        mov_conditions['small_cone_nogo'].object='small cone'
        # What is the distance?
        mov_conditions['small_cone_nogo'].object_distance=34.3
        mov_conditions['small_cone_nogo'].grasp=''
        mov_conditions['small_cone_nogo'].hand_visible=True
        mov_conditions['small_cone_nogo'].object_visible=True
        mov_conditions['small_cone_nogo'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe large cone whole hand grasp').count():
        obs_conditions['large_cone_go_light']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe large cone whole hand grasp')[0]
    else:
        obs_conditions['large_cone_go_light']=GraspObservationCondition()
        obs_conditions['large_cone_go_light'].experiment=exp
        obs_conditions['large_cone_go_light'].name='Observe large cone whole hand grasp'
        obs_conditions['large_cone_go_light'].description='Monkeys observed the human experimenter grasping a large cone '\
                                                          'using the whole hand by opposing all the fingers to the '\
                                                          'palm. The fixation point was presented and the monkey was '\
                                                          'required to start fixating it within 1.2 s. Fixation onset '\
                                                          'determined the presentation of a cue sound (a pure high '\
                                                          'tone constituted by a 1200 Hz sine wave). After 0.8 s, the '\
                                                          'upper sector of the box was illuminated and the '\
                                                          'experimenter\'s hand and a large cone became visible at a 90 '\
                                                          'degree angle. Then, after a variable time lag (0.8-1.2 s), '\
                                                          'the sound ceased (go signal) and the experimenter reached, '\
                                                          'grasped, and pulled the object within 1.2 s. Then the '\
                                                          'experimenter held the object steadily for at least 0.8 s. '\
                                                          'If the monkey did not break fixation, a juice reward was '\
                                                          'automatically delivered.'
        obs_conditions['large_cone_go_light'].type='grasp_observe'
        obs_conditions['large_cone_go_light'].object='large cone'
        obs_conditions['large_cone_go_light'].grasp='whole hand'
        # What is the distance?
        obs_conditions['large_cone_go_light'].object_distance=63.8
        obs_conditions['large_cone_go_light'].whole_body_visible=False
        obs_conditions['large_cone_go_light'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['large_cone_go_light'].demonstration_type='live'
        obs_conditions['large_cone_go_light'].viewing_angle=90.0
        obs_conditions['large_cone_go_light'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe large cone - nogo').count():
        obs_conditions['large_cone_nogo']=GraspObservationCondition.objects.using(db).filter(experiment=exp,name='Observe large cone - nogo')[0]
    else:
        obs_conditions['large_cone_nogo']=GraspObservationCondition()
        obs_conditions['large_cone_nogo'].experiment=exp
        obs_conditions['large_cone_nogo'].name='Observe large cone - nogo'
        obs_conditions['large_cone_nogo'].description='Monkeys observed the human experimenter\'s hand resting next to '\
                                                      'a large cone. The fixation point was presented and the monkey was '\
                                                      'required to start fixating it within 1.2 s. Fixation onset '\
                                                      'determined the presentation of a cue sound (a pure low tone '\
                                                      'constituted by a 300 Hz sine wave). After 0.8 s, the upper '\
                                                      'sector of the box was illuminated and the experimenter\'s hand '\
                                                      'and a large cone became visible. Then, after a variable time lag '\
                                                      '(0.8-1.2 s), the sound ceased and the monkey had to continue to '\
                                                      'maintain fixation for 1.2 s to receive a drop of juice as a '\
                                                      'reward.'
        obs_conditions['large_cone_nogo'].type='grasp_observe'
        obs_conditions['large_cone_nogo'].object='large cone'
        obs_conditions['large_cone_nogo'].grasp=''
        # What is the distance?
        obs_conditions['large_cone_nogo'].object_distance=63.8
        obs_conditions['large_cone_nogo'].whole_body_visible=False
        obs_conditions['large_cone_nogo'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_conditions['large_cone_nogo'].demonstration_type='live'
        obs_conditions['large_cone_nogo'].viewing_angle=90.0
        obs_conditions['large_cone_nogo'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute large cone whole hand grasp').count():
        mov_conditions['large_cone_go_light']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute large cone whole hand grasp')[0]
    else:
        mov_conditions['large_cone_go_light']=GraspPerformanceCondition()
        mov_conditions['large_cone_go_light'].experiment=exp
        mov_conditions['large_cone_go_light'].name='Execute large cone whole hand grasp'
        mov_conditions['large_cone_go_light'].description='Monkeys grasped a large cone using a the whole hand by opposing '\
                                                          'all the fingers to the palm. The fixation point was presented '\
                                                          'and the monkey was required to start fixating it within 1.2 s. '\
                                                          'Fixation onset determined the presentation of a cue sound (a '\
                                                          'pure high tone constituted by a 1200 Hz sine wave), which '\
                                                          'instructed the monkey to grasp the subsequently presented '\
                                                          'object. After 0.8 s, the lower sector of the box was '\
                                                          'illuminated and a large cone became visible. Then, after a '\
                                                          'variable time lag (0.8-1.2 s), the sound ceased (go signal) '\
                                                          'and the monkey had to reach, grasp, and pull the object within '\
                                                          '1.2 s. Then it had to hold the object steadily for at least '\
                                                          '0.8 s. If the task was performed correctly without breaking '\
                                                          'fixation, a juice reward was automatically delivered.'
        mov_conditions['large_cone_go_light'].type='grasp_perform'
        mov_conditions['large_cone_go_light'].object='large cone'
        # What is the distance?
        mov_conditions['large_cone_go_light'].object_distance=34.3
        mov_conditions['large_cone_go_light'].grasp='whole hand'
        mov_conditions['large_cone_go_light'].hand_visible=True
        mov_conditions['large_cone_go_light'].object_visible=True
        mov_conditions['large_cone_go_light'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute large cone whole hand grasp in the dark').count():
        mov_conditions['large_cone_go_dark']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Execute large cone whole hand grasp in the dark')[0]
    else:
        mov_conditions['large_cone_go_dark']=GraspPerformanceCondition()
        mov_conditions['large_cone_go_dark'].experiment=exp
        mov_conditions['large_cone_go_dark'].name='Execute large cone whole hand grasp in the dark'
        mov_conditions['large_cone_go_dark'].description='Monkeys grasped a large cone in the dark using a the whole hand by '\
                                                         'opposing all the fingers to the palm. The fixation point was '\
                                                         'presented and the monkey was required to start fixating it '\
                                                         'within 1.2 s. Fixation onset determined the presentation of a '\
                                                         'cue sound (a pure high tone constituted by a 1200 Hz sine wave), '\
                                                         'which instructed the monkey to grasp the subsequently presented '\
                                                         'object. After 0.8 s, the lower sector of the box was '\
                                                         'illuminated and a bing cone became visible. Then, after a '\
                                                         'variable time lag (0.8-1.2 s), the sound ceased (go signal) and '\
                                                         'the light inside the box was automatically turned off and the '\
                                                         'monkey performed the subsequent motor acts in complete darkness. '\
                                                         'The monkey had to reach, grasp, and pull the object within '\
                                                         '1.2 s. Then it had to hold the object steadily for at least '\
                                                         '0.8 s. If the task was performed correctly without breaking '\
                                                         'fixation, a juice reward was automatically delivered.'
        mov_conditions['large_cone_go_dark'].type='grasp_perform'
        mov_conditions['large_cone_go_dark'].object='large cone'
        # What is the distance?
        mov_conditions['large_cone_go_dark'].object_distance=34.3
        mov_conditions['large_cone_go_dark'].grasp='whole hand'
        mov_conditions['large_cone_go_dark'].hand_visible=False
        mov_conditions['large_cone_go_dark'].object_visible=False
        mov_conditions['large_cone_go_dark'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe large cone - nogo').count():
        mov_conditions['large_cone_nogo']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Observe large cone - nogo')[0]
    else:
        mov_conditions['large_cone_nogo']=GraspPerformanceCondition()
        mov_conditions['large_cone_nogo'].experiment=exp
        mov_conditions['large_cone_nogo'].name='Observe large cone - nogo'
        mov_conditions['large_cone_nogo'].description='Monkeys observed a large cone. The fixation point was presented '\
                                                      'and the monkey was required to start fixating it within 1.2 s. '\
                                                      'Fixation onset determined the presentation of a cue sound (a '\
                                                      'pure low tone constituted by a 300 Hz sine wave), which was '\
                                                      'associated with object fixation trials. After 0.8 s, the lower '\
                                                      'sector of the box was illuminated and a ring became visible. '\
                                                      'Then, after a variable time lag (0.8-1.2 s), the sound ceased '\
                                                      'and the monkey had to maintain fixation for 1.2 s to receive a '\
                                                      'drop of juice as a reward.'
        mov_conditions['large_cone_nogo'].type='grasp_perform'
        mov_conditions['large_cone_nogo'].object='large cone'
        # What is the distance?
        mov_conditions['large_cone_nogo'].object_distance=34.3
        mov_conditions['large_cone_nogo'].grasp=''
        mov_conditions['large_cone_nogo'].hand_visible=True
        mov_conditions['large_cone_nogo'].object_visible=True
        mov_conditions['large_cone_nogo'].save(using=db)


    pretrial_padding=0.25
    posttrial_padding=0.25

    for nex_idx, nex_file in enumerate(nex_files):
        r=io.NeuroExplorerIO(filename=nex_file)
        block=r.read(cascade=True, lazy=False)[0]
        for seg_idx, seg in enumerate(block.segments):
            print('importing segment %d' % seg_idx)

            events={}
            for idx,event_array in enumerate(seg.eventarrays):
                events[event_array.annotations['channel_name']]=idx

            units=[]
            for unit_idx,st in enumerate(seg.spiketrains):
                print('importing unit %s' % st.name)
                unit=Unit()
                area='F5'
                region=BrainRegion.objects.using(db).filter(Q(Q(name=area) | Q(abbreviation=area)))
                unit.area=region[0]
                unit.type='UID'
                unit.save(using=db)
                units.append(unit)

            # Iterate through epochs:
            for epoch_idx, epocharray in enumerate(seg.epocharrays):
                print('importing epoch %d' % epoch_idx)
                epoch_type=epocharray.annotations['channel_name']
                if not epoch_type=='AllFile':
                    trial_start_times=[]
                    trial_end_times=[]

                    epoch_start=epocharray.times[0]
                    epoch_end=epoch_start+epocharray.durations[0]

                    # nogo light ring trials
                    for time_idx,time in enumerate(seg.eventarrays[events['ev_01_LightON_visualCOR_RNG']].times):
                        if epoch_start <= time <= epoch_end:
                            nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                epoch_start, epoch_end)
                            nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                epoch_start, epoch_end)
                            if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                trial_start_times.append(nearest_fixation-pretrial_padding)
                                trial_end_times.append(nearest_reward+posttrial_padding)

                    for time in seg.eventarrays[events['ev_03_Pull_CORc1_RNG']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['ev_02_LightON_motorCORc1_RNG']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on,
                                    seg.eventarrays[events['EVT09']], epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # go dark ring trials
                    for time in seg.eventarrays[events['ev_04_Pull_CORc2_RNG']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['LightON_motorCORc2_RNG']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # nogo light small cone trials
                    for time_idx,time in enumerate(seg.eventarrays[events['ev_05_LightON_visualCOR_SML']].times):
                        if epoch_start <= time <= epoch_end:
                            nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                epoch_start, epoch_end)
                            nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                epoch_start, epoch_end)
                            if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                trial_start_times.append(nearest_fixation-pretrial_padding)
                                trial_end_times.append(nearest_reward+posttrial_padding)

                    # go light small cone trials
                    for time in seg.eventarrays[events['ev_07_Pull_CORc1_SML']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['ev_06_LightON_motorCORc1_SML']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # go dark small cone trials
                    for time in seg.eventarrays[events['ev_08_Pull_CORc2_SML']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['LightON_motorCORc2_SML']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # nogo light large cone trials
                    for time_idx,time in enumerate(seg.eventarrays[events['ev_09_LightON_visualCOR_BIG']].times):
                        if epoch_start <= time <= epoch_end:
                            nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                epoch_start, epoch_end)
                            nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                epoch_start, epoch_end)
                            if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                trial_start_times.append(nearest_fixation-pretrial_padding)
                                trial_end_times.append(nearest_reward+posttrial_padding)

                    # go light large cone trials
                    for time in seg.eventarrays[events['ev_11_Pull_CORc1_BIG']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['ev_10_LightON_motorCORc1_BIG']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # go dark large cone trials
                    for time in seg.eventarrays[events['ev_12_Pull_CORc2_BIG']].times:
                        if epoch_start <= time <= epoch_end:
                            nearest_light_on=find_nearest_event_before(time,
                                seg.eventarrays[events['LightON_motorCORc2_BIG']], epoch_start, epoch_end)
                            if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                    # iterate through trials
                    for trial_idx in range(len(trial_start_times)):
                        # create trial
                        trial=RecordingTrial()
                        trial.trial_number=trial_idx+1
                        trial.start_time=trial_start_times[trial_idx]
                        trial.end_time=trial_end_times[trial_idx]
                        trial.save(using=db)
                        print('importing trial %d, %.3f-%.3f' % (trial_idx,trial.start_time,trial.end_time))

                        for event,evt_idx in events.iteritems():
                            for evt_time in seg.eventarrays[evt_idx].times:
                                if trial.start_time <= evt_time < trial.end_time:
                                    # create trial events
                                    new_event=Event(name=event, description='', trial=trial, time=evt_time.rescale('s').magnitude.item(0))
                                    new_event.save(using=db)

                        condition_name=None
                        if Event.objects.using(db).filter(name='ev_01_LightON_visualCOR_RNG',trial=trial).count():
                            condition_name='ring_nogo'
                        elif Event.objects.using(db).filter(name='ev_02_LightON_motorCORc1_RNG',trial=trial).count():
                            condition_name='ring_go_light'
                        elif Event.objects.using(db).filter(name='ev_04_Pull_CORc2_RNG',trial=trial).count():
                            condition_name='ring_go_dark'

                        elif Event.objects.using(db).filter(name='ev_05_LightON_visualCOR_SML',trial=trial).count():
                            condition_name='small_cone_nogo'
                        elif Event.objects.using(db).filter(name='ev_06_LightON_motorCORc1_SML',trial=trial).count():
                            condition_name='small_cone_go_light'
                        elif Event.objects.using(db).filter(name='ev_08_Pull_CORc2_SML',trial=trial).count():
                            condition_name='small_cone_go_dark'

                        elif Event.objects.using(db).filter(name='ev_09_LightON_visualCOR_BIG',trial=trial).count():
                            condition_name='large_cone_nogo'
                        elif Event.objects.using(db).filter(name='ev_10_LightON_motorCORc1_BIG',trial=trial).count():
                            condition_name='large_cone_go_light'
                        elif Event.objects.using(db).filter(name='ev_12_Pull_CORc2_BIG',trial=trial).count():
                            condition_name='large_cone_go_dark'

                        if condition_name is not None:
                            if epoch_type=='OBSERVATION_TASK':
                                trial.condition=obs_conditions[condition_name]
                            elif epoch_type=='VISUOMOTOR_TASK':
                                trial.condition=mov_conditions[condition_name]
                            trial.save(using=db)
                            events_to_delete=[]
                            for event in Event.objects.using(db).filter(trial=trial):
                                old_evt_name=event.name
                                if old_evt_name in event_map:
                                    event.name=event_map[old_evt_name][0]
                                    event.description=event_map[old_evt_name][1]
                                    event.save(using=db)
                                else:
                                    events_to_delete.append(event.id)
                            Event.objects.using(db).filter(id__in=events_to_delete).delete()
                        else:
                            Event.objects.using(db).filter(trial=trial).delete()
                            trial.delete(using=db)

                        for unit_idx,st in enumerate(seg.spiketrains):
                            unit_recording=UnitRecording(unit=units[unit_idx], trial=trial)
                            spike_times=[]
                            for spike_time in st.rescale('s').magnitude:
                                if trial.start_time <= spike_time < trial.end_time:
                                    spike_times.append(spike_time)
                            if len(spike_times)>0:
                                unit_recording.spike_times=','.join([str(x) for x in sorted(spike_times)])
                            unit_recording.save(using=db)
    return exp


def find_nearest_event_before(event_time, event_array, epoch_start, epoch_end):
    nearest_time=0
    try:
        event_time=event_time.rescale('s').magnitude.item(0)
    except:
        pass
    for time_idx,time in enumerate(event_array.times):
        time=time.rescale('s').magnitude.item(0)
        if epoch_start <= time <= epoch_end:
            if time<event_time:
                diff=event_time-time
                if diff<event_time-nearest_time:
                    nearest_time=time
            else:
                break
    if nearest_time==0:
        return None
    return nearest_time


def find_nearest_event_after(event_time, event_array, epoch_start, epoch_end):
    try:
        event_time=event_time.rescale('s').magnitude.item(0)
    except:
        pass
    for time_idx,time in enumerate(event_array.times):
        time=time.rescale('s').magnitude.item(0)
        if epoch_start <= time <= epoch_end:
            if time>event_time:
                return time
    return None


def import_social_goal_mirror_data(db='default'):
    monkeys = ['Betta', 'Houdini']

    collator = User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='jbonaiuto').count():
        collator = User.objects.using(db).get(username='jbonaiuto')

    exp_title = 'F5 mirror neuron - Social goals'
    exp = Experiment()
    exp.collator = collator
    exp.last_modified_by = collator
    exp.title = exp_title
    exp.brief_description = 'Recording of unidentified F5 neurons while monkeys observed object-directed grasps'
    exp.save(using=db)
    print('importing experiment %d' % exp.id)

    demonstrator_species = Species.objects.using(db).get(genus_name='Homo', species_name='sapiens')

    conditions = {}
    if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Grasp to place in container').count():
        conditions['container'] = \
            GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Grasp to place in container')[0]
    else:
        conditions['container'] = GraspObservationCondition()
        conditions['container'].experiment = exp
        conditions['container'].name = 'Grasp to place in container'
        conditions['container'].description = ''
        conditions['container'].type = 'grasp_observe'
        conditions['container'].object = 'cube'
        conditions['container'].object_distance = 13
        conditions['container'].grasp = 'precision pinch'
        conditions['container'].demonstrator_species = demonstrator_species
        conditions['container'].demonstration_type = 'live'
        conditions['container'].viewing_angle = 180
        conditions['container'].whole_body_visible = True
        conditions['container'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Grasp to place in mouth').count():
        conditions['mouth'] = \
            GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Grasp to place in mouth')[0]
    else:
        conditions['mouth'] = GraspObservationCondition()
        conditions['mouth'].experiment = exp
        conditions['mouth'].name = 'Grasp to place in mouth'
        conditions['mouth'].description = ''
        conditions['mouth'].type = 'grasp_observe'
        conditions['mouth'].object = 'cube'
        conditions['mouth'].object_distance = 13
        conditions['mouth'].grasp = 'precision pinch'
        conditions['mouth'].demonstrator_species = demonstrator_species
        conditions['mouth'].demonstration_type = 'live'
        conditions['mouth'].viewing_angle = 180
        conditions['mouth'].whole_body_visible = True
        conditions['mouth'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,
                                                          name='Grasp to place in experimenter\'s hand').count():
        conditions['hand'] = GraspObservationCondition.objects.using(db).filter(experiment=exp,
                                                                                name='Grasp to place in experimenter\'s hand')[0]
    else:
        conditions['hand'] = GraspObservationCondition()
        conditions['hand'].experiment = exp
        conditions['hand'].name = 'Grasp to place in experimenter\'s hand'
        conditions['hand'].description = ''
        conditions['hand'].type = 'grasp_observe'
        conditions['hand'].object = 'cube'
        conditions['hand'].object_distance = 13
        conditions['hand'].grasp = 'precision pinch'
        conditions['hand'].demonstrator_species = demonstrator_species
        conditions['hand'].demonstration_type = 'live'
        conditions['hand'].viewing_angle = 180
        conditions['hand'].whole_body_visible = True
        conditions['hand'].save(using=db)

    if GraspObservationCondition.objects.using(db).filter(experiment=exp,
                                                          name='Grasp to place in monkey\'s hand').count():
        conditions['monkey'] = GraspObservationCondition.objects.using(db).filter(experiment=exp,
                                                                                name='Grasp to place in monkey\'s hand')[0]
    else:
        conditions['monkey'] = GraspObservationCondition()
        conditions['monkey'].experiment = exp
        conditions['monkey'].name = 'Grasp to place in monkey\'s hand'
        conditions['monkey'].description = ''
        conditions['monkey'].type = 'grasp_observe'
        conditions['monkey'].object = 'cube'
        conditions['monkey'].object_distance = 13
        conditions['monkey'].grasp = 'precision pinch'
        conditions['monkey'].demonstrator_species = demonstrator_species
        conditions['monkey'].demonstration_type = 'live'
        conditions['monkey'].viewing_angle = 180
        conditions['monkey'].whole_body_visible = True
        conditions['monkey'].save(using=db)

    for monkey in monkeys:
        print(monkey)
        subject=Subject(subj_id=monkey)
        subject.species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
        subject.save(using=db)

        penetration_dirs = glob('/home/bonaiuto/Dropbox/social_goal_mirror/data/%s*' % monkey)
        for dir_idx, penetration_dir in enumerate(penetration_dirs):
            (path, file) = os.path.split(penetration_dir)
            penetration_label=file[-2:]
            print(penetration_label)
            penetration = Penetration(label=penetration_label, subject=subject)
            penetration.save(using=db)

            mat_file = scipy.io.loadmat(os.path.join(penetration_dir,'spikes.mat'))

            hand_grasp_times=[]
            hand_fixation_times = []
            hand_exp_move_times = []
            hand_place_times=[]
            monkey_grasp_times=[]
            monkey_fixation_times=[]
            monkey_exp_move_times=[]
            monkey_place_times=[]
            monkey_rt_times=[]
            mouth_grasp_times=[]
            mouth_fixation_times=[]
            mouth_exp_move_times=[]
            mouth_place_times=[]
            container_grasp_times=[]
            container_fixation_times=[]
            container_exp_move_times=[]
            container_place_times=[]
            hand_trial_spikes=[]
            monkey_trial_spikes=[]
            mouth_trial_spikes=[]
            container_trial_spikes=[]
            unit_names=[]
            for list_idx,list_name in enumerate(mat_file['spike_data'].dtype.descr):
                if list_name[0]=='unit_names':
                    if len(mat_file['spike_data'][0][0][list_idx])>0:
                        unit_names=mat_file['spike_data'][0][0][list_idx][0]
                    else:
                        break
                elif list_name[0]=='hand_grasp_times':
                    hand_grasp_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='hand_fixation_times':
                    hand_fixation_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='hand_exp_move_times':
                    hand_exp_move_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='hand_place_times':
                    hand_place_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='monkey_grasp_times':
                    monkey_grasp_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='monkey_fixation_times':
                    monkey_fixation_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='monkey_exp_move_times':
                    monkey_exp_move_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='monkey_place_times':
                    monkey_place_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='monkey_rt_times':
                    monkey_rt_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='mouth_grasp_times':
                    mouth_grasp_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'mouth_fixation_times':
                    mouth_fixation_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'mouth_exp_move_times':
                    mouth_exp_move_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'mouth_place_times':
                    mouth_place_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0]=='container_grasp_times':
                    container_grasp_times=mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'container_fixation_times':
                    container_fixation_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'container_exp_move_times':
                    container_exp_move_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'container_place_times':
                    container_place_times = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'hand_trial_spikes':
                    hand_trial_spikes = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'monkey_trial_spikes':
                    monkey_trial_spikes = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'mouth_trial_spikes':
                    mouth_trial_spikes = mat_file['spike_data'][0][0][list_idx]
                elif list_name[0] == 'container_trial_spikes':
                    container_trial_spikes = mat_file['spike_data'][0][0][list_idx]

            units = []
            for unit_str in unit_names:
                print('importing unit %s' % unit_str[0])
                unit = Unit()
                unit.label = unit_str[0]
                unit.penetration = penetration
                area = 'F5'
                region = BrainRegion.objects.using(db).filter(Q(Q(name=area) | Q(abbreviation=area)))
                unit.area = region[0]
                unit.type = 'UID'
                unit.save(using=db)
                units.append(unit)

            for trial_idx in range(len(hand_fixation_times)):
                if len(hand_fixation_times[trial_idx])==1 and len(hand_exp_move_times[trial_idx])==1 and \
                        len(hand_grasp_times[trial_idx])==1 and len(hand_place_times[trial_idx])==1:
                    # create trial
                    trial = RecordingTrial()
                    trial.trial_number = trial_idx + 1
                    trial.start_time = -3
                    trial.end_time = 3
                    trial.condition = conditions['hand']
                    trial.save(using=db)
                    print('importing trial %d, %.3f-%.3f' % (trial_idx, trial.start_time, trial.end_time))

                    fixation_event = Event(name='fixation', description='', trial=trial,
                                      time=float(hand_fixation_times[trial_idx][0]))
                    fixation_event.save(using=db)

                    exp_move_event = Event(name='exp_move', description='', trial=trial,
                                           time=float(hand_exp_move_times[trial_idx][0]))
                    exp_move_event.save(using=db)

                    grasp_event = Event(name='grasp', description='', trial=trial,
                                           time=float(hand_grasp_times[trial_idx][0]))
                    grasp_event.save(using=db)

                    place_event = Event(name='place', description='', trial=trial,
                                        time=float(hand_place_times[trial_idx][0]))
                    place_event.save(using=db)

                    for unit_idx, unit in enumerate(units):
                        unit_recording = UnitRecording(unit=units[unit_idx], trial=trial)
                        spike_times = []

                        for spike_time in hand_trial_spikes[unit_idx][trial_idx]:
                            if len(spike_time)>0:
                                spike_times.append(spike_time[0])
                        if len(spike_times) > 0:
                            unit_recording.spike_times = ','.join([str(x) for x in sorted(spike_times)])
                        unit_recording.save(using=db)

            for trial_idx in range(len(monkey_fixation_times)):
                if len(monkey_fixation_times[trial_idx]) == 1 and len(monkey_exp_move_times[trial_idx]) == 1 and \
                        len(monkey_grasp_times[trial_idx]) == 1 and len(monkey_place_times[trial_idx]) == 1 and len(monkey_rt_times[trial_idx])==1:
                    # create trial
                    trial = RecordingTrial()
                    trial.trial_number = trial_idx + 1
                    trial.start_time = -3
                    trial.end_time = 3
                    trial.condition = conditions['monkey']
                    trial.save(using=db)
                    print('importing trial %d, %.3f-%.3f' % (trial_idx, trial.start_time, trial.end_time))

                    fixation_event = Event(name='fixation', description='', trial=trial,
                                      time=float(monkey_fixation_times[trial_idx][0]))
                    fixation_event.save(using=db)

                    exp_move_event = Event(name='exp_move', description='', trial=trial,
                                           time=float(monkey_exp_move_times[trial_idx][0]))
                    exp_move_event.save(using=db)

                    grasp_event = Event(name='grasp', description='', trial=trial,
                                           time=float(monkey_grasp_times[trial_idx][0]))
                    grasp_event.save(using=db)

                    rt_event = Event(name='rt', description='', trial=trial,
                                        time=float(monkey_rt_times[trial_idx][0]))
                    rt_event.save(using=db)

                    place_event = Event(name='place', description='', trial=trial,
                                        time=float(monkey_place_times[trial_idx][0]))
                    place_event.save(using=db)

                    for unit_idx, unit in enumerate(units):
                        unit_recording = UnitRecording(unit=units[unit_idx], trial=trial)
                        spike_times = []
                        for spike_time in monkey_trial_spikes[unit_idx][trial_idx]:
                            if len(spike_time) > 0:
                                spike_times.append(spike_time[0])
                        if len(spike_times) > 0:
                            unit_recording.spike_times = ','.join([str(x) for x in sorted(spike_times)])
                        unit_recording.save(using=db)

            for trial_idx in range(len(container_fixation_times)):
                if len(container_fixation_times[trial_idx]) == 1 and len(container_exp_move_times[trial_idx]) == 1 and len(
                        container_grasp_times[trial_idx]) == 1 and len(container_place_times[trial_idx]) == 1:
                    # create trial
                    trial = RecordingTrial()
                    trial.trial_number = trial_idx + 1
                    trial.start_time = -3
                    trial.end_time = 3
                    trial.condition = conditions['container']
                    trial.save(using=db)
                    print('importing trial %d, %.3f-%.3f' % (trial_idx, trial.start_time, trial.end_time))

                    fixation_event = Event(name='fixation', description='', trial=trial,
                                      time=float(container_fixation_times[trial_idx][0]))
                    fixation_event.save(using=db)

                    exp_move_event = Event(name='exp_move', description='', trial=trial,
                                           time=float(container_exp_move_times[trial_idx][0]))
                    exp_move_event.save(using=db)

                    grasp_event = Event(name='grasp', description='', trial=trial,
                                           time=float(container_grasp_times[trial_idx][0]))
                    grasp_event.save(using=db)

                    place_event = Event(name='place', description='', trial=trial,
                                        time=float(container_place_times[trial_idx][0]))
                    place_event.save(using=db)

                    for unit_idx, unit in enumerate(units):
                        unit_recording = UnitRecording(unit=units[unit_idx], trial=trial)
                        spike_times = []
                        for spike_time in container_trial_spikes[unit_idx][trial_idx]:
                            if len(spike_time) > 0:
                                spike_times.append(spike_time[0])
                        if len(spike_times) > 0:
                            unit_recording.spike_times = ','.join([str(x) for x in sorted(spike_times)])
                        unit_recording.save(using=db)

            for trial_idx in range(len(mouth_fixation_times)):
                if len(mouth_fixation_times[trial_idx]) == 1 and len(mouth_exp_move_times[trial_idx]) == 1 and \
                        len(mouth_grasp_times[trial_idx]) == 1 and len(mouth_place_times[trial_idx]) == 1:
                    # create trial
                    trial = RecordingTrial()
                    trial.trial_number = trial_idx + 1
                    trial.start_time = -3
                    trial.end_time = 3
                    trial.condition = conditions['mouth']
                    trial.save(using=db)
                    print('importing trial %d, %.3f-%.3f' % (trial_idx, trial.start_time, trial.end_time))

                    fixation_event = Event(name='fixation', description='', trial=trial,
                                      time=float(mouth_fixation_times[trial_idx][0]))
                    fixation_event.save(using=db)

                    exp_move_event = Event(name='exp_move', description='', trial=trial,
                                           time=float(mouth_exp_move_times[trial_idx][0]))
                    exp_move_event.save(using=db)

                    grasp_event = Event(name='grasp', description='', trial=trial,
                                           time=float(mouth_grasp_times[trial_idx][0]))
                    grasp_event.save(using=db)

                    place_event = Event(name='place', description='', trial=trial,
                                        time=float(mouth_place_times[trial_idx][0]))
                    place_event.save(using=db)

                    for unit_idx, unit in enumerate(units):
                        unit_recording = UnitRecording(unit=units[unit_idx], trial=trial)
                        spike_times = []
                        for spike_time in mouth_trial_spikes[unit_idx][trial_idx]:
                            if len(spike_time) > 0:
                                spike_times.append(spike_time[0])
                        if len(spike_times) > 0:
                            unit_recording.spike_times = ','.join([str(x) for x in sorted(spike_times)])
                        unit_recording.save(using=db)

    try:
        rebuild_index.Command().handle(interactive=False)
    except:
        pass


def import_tool_exp_data(subj_name, date, db='default'):
    recording_date = datetime.strptime(date, '%d.%m.%y')

    collator = User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='jbonaiuto').count():
        collator = User.objects.using(db).get(username='jbonaiuto')

    exp_title='Tool use experiment'
    if Experiment.objects.using(db).filter(title=exp_title).count():
        exp=Experiment.objects.using(db).get(title=exp_title)
        print('using experiment %d' % exp.id)
    else:
        exp=Experiment()
        exp.collator=collator
        exp.last_modified_by=collator
        exp.title=exp_title
        exp.brief_description='Recording of F1, F5hand, F5mouth, F2, 45v/12r, and 45a neurons while monkeys perform grasps, use rake, observe grasps, and observe multiple tool actions'
        exp.save(using=db)
        print('importing experiment %d' % exp.id)

    demonstrator_species = Species.objects.using(db).get(genus_name='Homo', species_name='sapiens')

    conditions={}
    # if GraspPerformanceCondition.objects.using(db).filter(experiment=exp, name='Grasp left object with hand').count():
    #     conditions['motor_grasp_left']=GraspPerformanceCondition.objects.using(db).get(experiment=exp, name='Grasp left object with hand')
    # else:
    #     conditions['motor_grasp_left']=GraspPerformanceCondition()
    #     conditions['motor_grasp_left'].experiment=exp
    #     conditions['motor_grasp_left'].name='Grasp left object with hand'
    #     conditions['motor_grasp_left'].description=''
    #     conditions['motor_grasp_left'].type = 'grasp_perform'
    #     conditions['motor_grasp_left'].object = 'cube'
    #     conditions['motor_grasp_left'].object_distance = 13
    #     conditions['motor_grasp_left'].grasp = 'precision pinch'
    #     conditions['motor_grasp_left'].hand_visible = True
    #     conditions['motor_grasp_left'].object_visible = True
    #     conditions['motor_grasp_left'].save(using=db)
    # if GraspPerformanceCondition.objects.using(db).filter(experiment=exp, name='Grasp center object with hand').count():
    #     conditions['motor_grasp_center']=GraspPerformanceCondition.objects.using(db).get(experiment=exp, name='Grasp center object with hand')
    # else:
    #     conditions['motor_grasp_center']=GraspPerformanceCondition()
    #     conditions['motor_grasp_center'].experiment=exp
    #     conditions['motor_grasp_center'].name='Grasp center object with hand'
    #     conditions['motor_grasp_center'].description=''
    #     conditions['motor_grasp_center'].type = 'grasp_perform'
    #     conditions['motor_grasp_center'].object = 'cube'
    #     conditions['motor_grasp_center'].object_distance = 13
    #     conditions['motor_grasp_center'].grasp = 'precision pinch'
    #     conditions['motor_grasp_center'].hand_visible = True
    #     conditions['motor_grasp_center'].object_visible = True
    #     conditions['motor_grasp_center'].save(using=db)
    # if GraspPerformanceCondition.objects.using(db).filter(experiment=exp, name='Grasp right object with hand').count():
    #     conditions['motor_grasp_right']=GraspPerformanceCondition.objects.using(db).get(experiment=exp, name='Grasp right object with hand')
    # else:
    #     conditions['motor_grasp_right']=GraspPerformanceCondition()
    #     conditions['motor_grasp_right'].experiment=exp
    #     conditions['motor_grasp_right'].name='Grasp center object with hand'
    #     conditions['motor_grasp_right'].description=''
    #     conditions['motor_grasp_right'].type = 'grasp_perform'
    #     conditions['motor_grasp_right'].object = 'cube'
    #     conditions['motor_grasp_right'].object_distance = 13
    #     conditions['motor_grasp_right'].grasp = 'precision pinch'
    #     conditions['motor_grasp_right'].hand_visible = True
    #     conditions['motor_grasp_right'].object_visible = True
    #     conditions['motor_grasp_right'].save(using=db)
    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp, name='Grasp object with hand').count():
        conditions['motor_grasp']=GraspPerformanceCondition.objects.using(db).get(experiment=exp, name='Grasp object with hand')
    else:
        conditions['motor_grasp']=GraspPerformanceCondition()
        conditions['motor_grasp'].experiment=exp
        conditions['motor_grasp'].name='Grasp object with hand'
        conditions['motor_grasp'].description=''
        conditions['motor_grasp'].type = 'grasp_perform'
        conditions['motor_grasp'].object = 'cube'
        conditions['motor_grasp'].object_distance = 13
        conditions['motor_grasp'].grasp = 'precision pinch'
        conditions['motor_grasp'].hand_visible = True
        conditions['motor_grasp'].object_visible = True
        conditions['motor_grasp'].save(using=db)
    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with hand from right').count():
    #     conditions['visual_grasp_right']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with hand from right')
    # else:
    #     conditions['visual_grasp_right'] = GraspObservationCondition()
    #     conditions['visual_grasp_right'].experiment = exp
    #     conditions['visual_grasp_right'].name = 'Observe grasp with hand from right'
    #     conditions['visual_grasp_right'].description = ''
    #     conditions['visual_grasp_right'].type = 'grasp_observe'
    #     conditions['visual_grasp_right'].object = 'cube'
    #     conditions['visual_grasp_right'].object_distance = 13
    #     conditions['visual_grasp_right'].grasp = 'precision pinch'
    #     conditions['visual_grasp_right'].demonstrator_species = demonstrator_species
    #     conditions['visual_grasp_right'].demonstration_type = 'live'
    #     conditions['visual_grasp_right'].viewing_angle = 90
    #     conditions['visual_grasp_right'].whole_body_visible = True
    #     conditions['visual_grasp_right'].save(using=db)
    #
    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with hand from left').count():
    #     conditions['visual_grasp_left']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with hand from left')
    # else:
    #     conditions['visual_grasp_left'] = GraspObservationCondition()
    #     conditions['visual_grasp_left'].experiment = exp
    #     conditions['visual_grasp_left'].name = 'Observe grasp with hand from left'
    #     conditions['visual_grasp_left'].description = ''
    #     conditions['visual_grasp_left'].type = 'grasp_observe'
    #     conditions['visual_grasp_left'].object = 'cube'
    #     conditions['visual_grasp_left'].object_distance = 13
    #     conditions['visual_grasp_left'].grasp = 'precision pinch'
    #     conditions['visual_grasp_left'].demonstrator_species = demonstrator_species
    #     conditions['visual_grasp_left'].demonstration_type = 'live'
    #     conditions['visual_grasp_left'].viewing_angle = -90
    #     conditions['visual_grasp_left'].whole_body_visible = True
    #     conditions['visual_grasp_left'].save(using=db)
    if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with hand').count():
        conditions['visual_grasp']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with hand')
    else:
        conditions['visual_grasp'] = GraspObservationCondition()
        conditions['visual_grasp'].experiment = exp
        conditions['visual_grasp'].name = 'Observe grasp with hand'
        conditions['visual_grasp'].description = ''
        conditions['visual_grasp'].type = 'grasp_observe'
        conditions['visual_grasp'].object = 'cube'
        conditions['visual_grasp'].object_distance = 13
        conditions['visual_grasp'].grasp = 'precision pinch'
        conditions['visual_grasp'].demonstrator_species = demonstrator_species
        conditions['visual_grasp'].demonstration_type = 'live'
        conditions['visual_grasp'].viewing_angle = -90
        conditions['visual_grasp'].whole_body_visible = True
        conditions['visual_grasp'].save(using=db)
        
    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with pliers from right').count():
    #     conditions['visual_pliers_right']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with pliers from right')
    # else:
    #     conditions['visual_pliers_right'] = GraspObservationCondition()
    #     conditions['visual_pliers_right'].experiment = exp
    #     conditions['visual_pliers_right'].name = 'Observe grasp with pliers from right'
    #     conditions['visual_pliers_right'].description = ''
    #     conditions['visual_pliers_right'].type = 'grasp_observe'
    #     conditions['visual_pliers_right'].object = 'cube'
    #     conditions['visual_pliers_right'].object_distance = 13
    #     conditions['visual_pliers_right'].grasp = 'precision pinch'
    #     conditions['visual_pliers_right'].demonstrator_species = demonstrator_species
    #     conditions['visual_pliers_right'].demonstration_type = 'live'
    #     conditions['visual_pliers_right'].viewing_angle = 90
    #     conditions['visual_pliers_right'].whole_body_visible = True
    #     conditions['visual_pliers_right'].save(using=db)
    #
    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with pliers from left').count():
    #     conditions['visual_pliers_left']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with pliers from left')
    # else:
    #     conditions['visual_pliers_left'] = GraspObservationCondition()
    #     conditions['visual_pliers_left'].experiment = exp
    #     conditions['visual_pliers_left'].name = 'Observe grasp with pliers from left'
    #     conditions['visual_pliers_left'].description = ''
    #     conditions['visual_pliers_left'].type = 'grasp_observe'
    #     conditions['visual_pliers_left'].object = 'cube'
    #     conditions['visual_pliers_left'].object_distance = 13
    #     conditions['visual_pliers_left'].grasp = 'precision pinch'
    #     conditions['visual_pliers_left'].demonstrator_species = demonstrator_species
    #     conditions['visual_pliers_left'].demonstration_type = 'live'
    #     conditions['visual_pliers_left'].viewing_angle = -90
    #     conditions['visual_pliers_left'].whole_body_visible = True
    #     conditions['visual_pliers_left'].save(using=db)
    if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe grasp with pliers').count():
        conditions['visual_pliers']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe grasp with pliers')
    else:
        conditions['visual_pliers'] = GraspObservationCondition()
        conditions['visual_pliers'].experiment = exp
        conditions['visual_pliers'].name = 'Observe grasp with pliers'
        conditions['visual_pliers'].description = ''
        conditions['visual_pliers'].type = 'grasp_observe'
        conditions['visual_pliers'].object = 'cube'
        conditions['visual_pliers'].object_distance = 13
        conditions['visual_pliers'].grasp = 'precision pinch'
        conditions['visual_pliers'].demonstrator_species = demonstrator_species
        conditions['visual_pliers'].demonstration_type = 'live'
        conditions['visual_pliers'].viewing_angle = -90
        conditions['visual_pliers'].whole_body_visible = True
        conditions['visual_pliers'].save(using=db)

    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe rake pull from right').count():
    #     conditions['visual_rake_pull_right']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe rake pull from right')
    # else:
    #     conditions['visual_rake_pull_right'] = GraspObservationCondition()
    #     conditions['visual_rake_pull_right'].experiment = exp
    #     conditions['visual_rake_pull_right'].name = 'Observe rake pull from right'
    #     conditions['visual_rake_pull_right'].description = ''
    #     conditions['visual_rake_pull_right'].type = 'grasp_observe'
    #     conditions['visual_rake_pull_right'].object = 'cube'
    #     conditions['visual_rake_pull_right'].object_distance = 13
    #     conditions['visual_rake_pull_right'].grasp = 'pull'
    #     conditions['visual_rake_pull_right'].demonstrator_species = demonstrator_species
    #     conditions['visual_rake_pull_right'].demonstration_type = 'live'
    #     conditions['visual_rake_pull_right'].viewing_angle = 90
    #     conditions['visual_rake_pull_right'].whole_body_visible = True
    #     conditions['visual_rake_pull_right'].save(using=db)
    #
    # if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe rake pull from left').count():
    #     conditions['visual_rake_pull_left']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe rake pull from left')
    # else:
    #     conditions['visual_rake_pull_left'] = GraspObservationCondition()
    #     conditions['visual_rake_pull_left'].experiment = exp
    #     conditions['visual_rake_pull_left'].name = 'Observe rake pull from left'
    #     conditions['visual_rake_pull_left'].description = ''
    #     conditions['visual_rake_pull_left'].type = 'grasp_observe'
    #     conditions['visual_rake_pull_left'].object = 'cube'
    #     conditions['visual_rake_pull_left'].object_distance = 13
    #     conditions['visual_rake_pull_left'].grasp = 'pull'
    #     conditions['visual_rake_pull_left'].demonstrator_species = demonstrator_species
    #     conditions['visual_rake_pull_left'].demonstration_type = 'live'
    #     conditions['visual_rake_pull_left'].viewing_angle = -90
    #     conditions['visual_rake_pull_left'].whole_body_visible = True
    #     conditions['visual_rake_pull_left'].save(using=db)
    if GraspObservationCondition.objects.using(db).filter(experiment=exp, name='Observe rake pull').count():
        conditions['visual_rake_pull']=GraspObservationCondition.objects.using(db).get(experiment=exp, name='Observe rake pull')
    else:
        conditions['visual_rake_pull'] = GraspObservationCondition()
        conditions['visual_rake_pull'].experiment = exp
        conditions['visual_rake_pull'].name = 'Observe rake pull'
        conditions['visual_rake_pull'].description = ''
        conditions['visual_rake_pull'].type = 'grasp_observe'
        conditions['visual_rake_pull'].object = 'cube'
        conditions['visual_rake_pull'].object_distance = 13
        conditions['visual_rake_pull'].grasp = 'pull'
        conditions['visual_rake_pull'].demonstrator_species = demonstrator_species
        conditions['visual_rake_pull'].demonstration_type = 'live'
        conditions['visual_rake_pull'].viewing_angle = -90
        conditions['visual_rake_pull'].whole_body_visible = True
        conditions['visual_rake_pull'].save(using=db)

    condition_map={
        'visual_grasp_left':'visual_grasp',
        'visual_grasp_right': 'visual_grasp',
        'visual_pliers_left': 'visual_pliers',
        'visual_pliers_right': 'visual_pliers',
        'visual_rake_pull_left': 'visual_rake_pull',
        'visual_rake_pull_right': 'visual_rake_pull',
        'motor_grasp_left': 'motor_grasp',
        'motor_grasp_center': 'motor_grasp',
        'motor_grasp_right': 'motor_grasp',
    }
    if Subject.objects.using(db).filter(subj_id=subj_name).count():
        subject=Subject.objects.using(db).get(subj_id=subj_name)
    else:
        subject = Subject(subj_id=subj_name)
        subject.species = Species.objects.using(db).get(genus_name='Macaca', species_name='mulatta')
        subject.save(using=db)

    # Reads trial info and events
    data_dir = os.path.join('/home/bonaiuto/Projects/tool_learning/data/preprocessed_data/', subj_name, date)
    trial_info=pd.read_csv(os.path.join(data_dir,'trial_info.csv'))
    trial_events=pd.read_csv(os.path.join(data_dir,'trial_events.csv'))

    arrays = ['F1', 'F5hand', 'F5mouth', '46v-12r', '45a', 'F2']

    trials=[]

    evt_dict={'visual_grasp': { 'exp_place_right': 'plc',
                                      'exp_grasp_center': 'o_on',
                                      'exp_place_left': 'plc',
                                      'reward': 'rew',
                                      'error': 'err',
                                      'exp_start_off': 's_off',
                                      'laser_exp_start_center': 'fix',
                                      'manual_reward': 'rew',
                                      'manual_error': 'err',
                                      'go':'go'},
              'visual_pliers': { 'exp_place_right': 'plc',
                                     'exp_grasp_center': 'o_on',
                                     'exp_place_left': 'plc',
                                     'reward': 'rew',
                                     'error': 'err',
                                     'exp_start_off': 's_off',
                                     'laser_exp_start_center': 'fix',
                                     'manual_reward': 'rew',
                                     'manual_error': 'err',
                                     'go': 'go'},
              'visual_rake_pull': {'exp_place_right': 'plc',
                                'exp_grasp_center': 'o_on',
                                'exp_place_left': 'plc',
                                'reward': 'rew',
                                'error': 'err',
                                'exp_start_off': 's_off',
                                'laser_exp_start_center': 'fix',
                                'manual_reward': 'rew',
                                'manual_error': 'err',
                                'go': 'go'},
             'motor_grasp': { 'monkey_handle_on': 's_on',
                                      'trap_edge': 'o_on',
                                      'trap_bottom': 'plc',
                                      'reward': 'rew',
                                      'error': 'err',
                                      'monkey_handle_off': 's_off',
                                      'manual_reward': 'rew',
                                      'manual_error': 'err',
                                      'go':'go',
                                      'laser_monkey_tool_center': 'fix'}
             }

    for index, row in trial_info.iterrows():

        # create trial
        trial = RecordingTrial()
        trial.date=recording_date
        trial.condition=conditions[condition_map[row['condition']]]

        # Figure out if correct trial
        if row['correct']:
            # Figure out global trial number
            global_trial_idx = 1
            if RecordingTrial.objects.using(db).filter(condition__experiment=trial.condition.experiment).count():
                global_trial_idx = RecordingTrial.objects.using(db).filter(condition__experiment=trial.condition.experiment).aggregate(Max('trial_number'))['trial_number__max'] + 1
            trial.trial_number = global_trial_idx


            # Figure out what rows have trial events
            evt_trial_rows = np.where(trial_events.trial == row['trial'])[0]

            # Get start and end times
            for row_idx in evt_trial_rows:
                evt_code = trial_events.event[row_idx]
                evt_time = trial_events.time[row_idx]/1000.0
                if evt_code == 'trial_start':
                    trial.start_time = evt_time
                elif evt_code == 'trial_stop':
                    trial.end_time = evt_time+1

            print('importing trial %d, %.3f-%.3f' % (row['trial'], trial.start_time, trial.end_time))
            trial.save(using=db)

            # Add events
            for row_idx in evt_trial_rows:
                evt_code = trial_events.event[row_idx]
                evt_time = trial_events.time[row_idx]/1000.0
                if not (evt_code == 'trial_start' or evt_code == 'trial_stop') and evt_code in evt_dict[condition_map[row['condition']]]:
                    trans_evt_code=evt_dict[condition_map[row['condition']]][evt_code]
                    new_event = Event(name=trans_evt_code, description=trans_evt_code, trial=trial, time=evt_time)
                    new_event.save(using=db)

        trials.append(trial)

    # Import spikes
    for array_idx, region in enumerate(arrays):

        if Array.objects.using(db).filter(label=region).count():
            array = Array.objects.using(db).get(label=region)
        else:
            array = Array(label=region, subject=subject)
            array.save()

        fnames=glob(os.path.join(data_dir,'%s*.csv' % region))
        for fname in fnames:
            electrode=os.path.split(fname)[1].split('_')[1]
            electrode_df=pd.read_csv(fname)
            for label_id in np.unique(electrode_df.cell):
                if label_id>=0:
                    unit_label='%s-%d' % (electrode,label_id)
                    if Unit.objects.using(db).filter(label=unit_label, array=array).count():
                        unit = Unit.objects.using(db).get(label=unit_label, array=array)
                    else:
                        print('importing unit %s' % unit_label)
                        unit = Unit()
                        unit.label = unit_label
                        unit.array = array
                        if BrainRegion.objects.using(db).filter(Q(Q(name=region) | Q(abbreviation=region))):
                            region = BrainRegion.objects.using(db).filter(Q(Q(name=region) | Q(abbreviation=region)))[0]
                        else:
                            if Nomenclature.objects.using(db).filter(name='Parma').count():
                                nomenclature = Nomenclature.objects.using(db).get(name='Parma')
                            else:
                                nomenclature = Nomenclature(name='Parma', version='1')
                                nomenclature.save()
                            region = BrainRegion(name=region, abbreviation=region,
                                                 brain_region_type='neural region',
                                                 nomenclature=nomenclature)
                            region.save()
                        unit.area = region
                        unit.type = 'UID'
                        unit.save(using=db)

                    unit_rows=np.where(electrode_df.cell==label_id)[0]
                    for trial_idx in np.unique(electrode_df.trial[unit_rows]):
                        if trial_info.correct[trial_idx]:
                            unit_trial_rows=np.where((electrode_df.cell==label_id) & (electrode_df.trial==trial_idx))[0]
                            unit_trial_spike_times=electrode_df.time[unit_trial_rows]/1000.0

                            unit_recording = UnitRecording(unit=unit, trial=trials[trial_idx])
                            if isinstance(unit_trial_spike_times,np.float64):
                                unit_recording.spike_times =str(unit_trial_spike_times)
                            else:
                                unit_recording.spike_times = ','.join([str(x) for x in sorted(unit_trial_spike_times)])
                            unit_recording.save(using=db)



def import_social_goal_data(db='default'):
    monkeys=['betta','houdini']

    collator=User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='jbonaiuto').count():
        collator=User.objects.using(db).get(username='jbonaiuto')

    event_map={
        'mo1MotorContainer':('oc','object contact'),
        'mo1MotorHand':('oc','object contact'),
        'mo1MotorMouth': ('oc','object contact'),
        'mo1MotorContainer_base': ('mo','movement onset'),
        'mo1MotorHand_base': ('mo','movement onset'),
        'mo1MotorMouth_base': ('mo','movement onset'),
        }

    exp_title='F5 mirror neuron - Social goals'
    exp=Experiment()
    exp.collator=collator
    exp.last_modified_by=collator
    exp.title=exp_title
    exp.brief_description='Recording of unidentified F5 neurons while monkeys observed or performed object-directed grasps'
    exp.save(using=db)
    print('importing experiment %d' % exp.id)

    conditions={}
    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in container').count():
        conditions['container']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in container')[0]
    else:
        conditions['container']=GraspPerformanceCondition()
        conditions['container'].experiment=exp
        conditions['container'].name='Grasp to place in container'
        conditions['container'].description='The monkey was seated facing a table (60X60 cm) onto which a metallic '\
                                            'cube was placed along the monkey body midline, at 13 cm from monkey\'s '\
                                            'hand starting position. The monkey had to reach and grasp the object '\
                                            'and then place it in a small container located 10 cm to the left of the '\
                                            'grasping location. At the beginning of each trial the monkey had to keep '\
                                            'the right hand on a handle attached to the table for at least 1000 ms, '\
                                            'after which, a transparent barrier was removed to give the "go" signal '\
                                            'and the monkey grasped the object and placed it in the container. A juice '\
                                            'reward (and a solid food reward) was delivered after 500-1000 ms, if the '\
                                            'monkey correctly executed the trial.'
        conditions['container'].type='grasp_perform'
        conditions['container'].object='cube'
        conditions['container'].object_distance=13
        conditions['container'].grasp='precision pinch'
        conditions['container'].hand_visible=True
        conditions['container'].object_visible=True
        conditions['container'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in mouth').count():
        conditions['mouth']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in mouth')[0]
    else:
        conditions['mouth']=GraspPerformanceCondition()
        conditions['mouth'].experiment=exp
        conditions['mouth'].name='Grasp to place in mouth'
        conditions['mouth'].description='The monkey was seated facing a table (60X60 cm) onto which a metallic '\
                                        'cube was placed along the monkey body midline, at 13 cm from monkey\'s '\
                                        'hand starting position. The monkey had to reach and grasp the object '\
                                        'and bring it to its mouth and eat it. At the beginning of each trial the monkey had to keep '\
                                        'the right hand on a handle attached to the table for at least 1000 ms, '\
                                        'after which, a transparent barrier was removed to give the "go" signal '\
                                        'and the monkey grasped the object and placed it in its mouth. A juice '\
                                        'reward was delivered after 500-1000 ms, if the '\
                                        'monkey correctly executed the trial.'
        conditions['mouth'].type='grasp_perform'
        conditions['mouth'].object='cube'
        conditions['mouth'].object_distance=13
        conditions['mouth'].grasp='precision pinch'
        conditions['mouth'].hand_visible=False
        conditions['mouth'].object_visible=False
        conditions['mouth'].save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in experimenter\'s hand').count():
        conditions['hand']=GraspPerformanceCondition.objects.using(db).filter(experiment=exp,name='Grasp to place in experimenter\'s hand')[0]
    else:
        conditions['hand']=GraspPerformanceCondition()
        conditions['hand'].experiment=exp
        conditions['hand'].name='Grasp to place in experimenter\'s hand'
        conditions['hand'].description='The monkey was seated facing a table (60X60 cm) onto which a metallic '\
                                       'cube was placed along the monkey body midline, at 13 cm from monkey\'s '\
                                       'hand starting position. The monkey had to reach and grasp the object '\
                                       'and then place it in the hand of the experimenter. At the beginning of each trial the monkey had to keep '\
                                       'the right hand on a handle attached to the table for at least 1000 ms, '\
                                       'after which, a transparent barrier was removed to give the "go" signal '\
                                       'and the monkey grasped the object and placed it in the experimenter\'s hand. A juice '\
                                       'reward (and a solid food reward) was delivered after 500-1000 ms, if the '\
                                       'monkey correctly executed the trial.'
        conditions['hand'].type='grasp_perform'
        conditions['hand'].object='cube'
        conditions['hand'].object_distance=13
        conditions['hand'].grasp='precision pinch'
        conditions['hand'].hand_visible=True
        conditions['hand'].object_visible=True
        conditions['hand'].save(using=db)

    for monkey in monkeys:

        subject=Subject(subj_id=monkey)
        subject.species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
        subject.save(using=db)

        nex_files=glob('/home/jbonaiuto/Projects/sensorimotordb/project/data/ferrari/%s*.nex' % monkey)
        for nex_idx, nex_file in enumerate(nex_files):

            (path,file)=os.path.split(nex_file)
            (file,ext)=os.path.splitext(file)
            penetration_label=file.split('_')[1][3:]
            penetration=Penetration(label=penetration_label, subject=subject)
            penetration.save(using=db)

            r=io.NeuroExplorerIO(filename=nex_file)
            block=r.read(cascade=True, lazy=False)[0]
            for seg_idx, seg in enumerate(block.segments):
                print('importing segment %d' % seg_idx)

                events={}
                for idx,event_array in enumerate(seg.eventarrays):
                    events[event_array.annotations['channel_name']]=idx

                units=[]
                for unit_idx,st in enumerate(seg.spiketrains):
                    print('importing unit %s' % st.name)
                    unit=Unit()
                    unit.label=st.name
                    unit.penetration=penetration
                    area='F5'
                    region=BrainRegion.objects.using(db).filter(Q(Q(name=area) | Q(abbreviation=area)))
                    unit.area=region[0]
                    unit.type='UID'
                    unit.save(using=db)
                    units.append(unit)

                # Iterate through epochs:
                for epoch_idx, epocharray in enumerate(seg.epocharrays):
                    epoch_type=epocharray.annotations['channel_name']
                    if epoch_type=='AllFile':
                        trial_start_times=[]
                        trial_end_times=[]

                        epoch_start=epocharray.times[0]
                        epoch_end=epoch_start+epocharray.durations[0]

                        # container
                        for time_idx,time in enumerate(seg.eventarrays[events['mo1MotorContainer_base']].times):
                            if epoch_start <= time <= epoch_end:
                                nearest_oc=find_nearest_event_after(time, seg.eventarrays[events['mo1MotorContainer']],
                                    epoch_start, epoch_end)
                                if nearest_oc is not None:
                                    trial_start_times.append(time.rescale('s').magnitude.item(0)-1.0)
                                    trial_end_times.append(nearest_oc+1.0)

                        # hand
                        for time in seg.eventarrays[events['mo1MotorHand_base']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_oc=find_nearest_event_after(time, seg.eventarrays[events['mo1MotorHand']],
                                    epoch_start, epoch_end)
                                if nearest_oc is not None:
                                    trial_start_times.append(time.rescale('s').magnitude.item(0)-1.0)
                                    trial_end_times.append(nearest_oc+1.0)

                        # mouth
                        for time in seg.eventarrays[events['mo1MotorMouth_base']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_oc=find_nearest_event_after(time, seg.eventarrays[events['mo1MotorMouth']],
                                    epoch_start, epoch_end)
                                if nearest_oc is not None:
                                    trial_start_times.append(time.rescale('s').magnitude.item(0)-1.0)
                                    trial_end_times.append(nearest_oc+1.0)

                        # iterate through trials
                        for trial_idx in range(len(trial_start_times)):
                            # create trial
                            trial=RecordingTrial()
                            trial.trial_number=trial_idx+1
                            trial.start_time=trial_start_times[trial_idx]
                            trial.end_time=trial_end_times[trial_idx]
                            trial.save(using=db)
                            print('importing trial %d, %.3f-%.3f' % (trial_idx,trial.start_time,trial.end_time))

                            for event,evt_idx in events.iteritems():
                                for evt_time in seg.eventarrays[evt_idx].times:
                                    if trial.start_time <= evt_time < trial.end_time:
                                        # create trial events
                                        if not Event.objects.filter(name=event, description='', trial=trial,
                                            time=evt_time.rescale('s').magnitude.item(0)).exists():
                                            new_event=Event(name=event, description='', trial=trial,
                                                time=evt_time.rescale('s').magnitude.item(0))
                                            new_event.save(using=db)

                            condition_name=None
                            if Event.objects.using(db).filter(name='mo1MotorContainer',trial=trial).count():
                                condition_name='container'
                            elif Event.objects.using(db).filter(name='mo1MotorHand',trial=trial).count():
                                condition_name='hand'
                            elif Event.objects.using(db).filter(name='mo1MotorMouth',trial=trial).count():
                                condition_name='mouth'

                            if condition_name is not None:
                                trial.condition=conditions[condition_name]
                                trial.save(using=db)
                                events_to_delete=[]
                                for event in Event.objects.using(db).filter(trial=trial):
                                    old_evt_name=event.name
                                    if old_evt_name in event_map:
                                        event.name=event_map[old_evt_name][0]
                                        event.description=event_map[old_evt_name][1]
                                        event.save(using=db)
                                    else:
                                        events_to_delete.append(event.id)
                                Event.objects.using(db).filter(id__in=events_to_delete).delete()
                            else:
                                Event.objects.using(db).filter(trial=trial).delete()
                                trial.delete(using=db)

                            for unit_idx,st in enumerate(seg.spiketrains):
                                unit_recording=UnitRecording(unit=units[unit_idx], trial=trial)
                                spike_times=[]
                                for spike_time in st.rescale('s').magnitude:
                                    if trial.start_time <= spike_time < trial.end_time:
                                        spike_times.append(spike_time)
                                if len(spike_times)>0:
                                    unit_recording.spike_times=','.join([str(x) for x in sorted(spike_times)])
                                unit_recording.save(using=db)


if __name__=='__main__':
    django.setup()
    remove_all()
    #dates=['20.11.18','21.11.18','26.11.18','27.11.18','28.11.18','29.11.18','30.11.18']
    dates=['08.03.19']
    for date in dates:
        print('*******************import date  %s ****************' % date)
        import_tool_exp_data('betta',date)
#    import_kraskov_data('data/kraskov/units4BODB.mat','data/kraskov/')
#    sed=import_bonini_data(['data/bonini/01_PIC_F5_09022012_mot_mirror_mrgSORTED.nex',
#                            'data/bonini/02_Pic_F5_10022012_mot_mirror_mrgSORTED.nex'])
    #import_social_goal_data()
    #import_social_goal_mirror_data()
