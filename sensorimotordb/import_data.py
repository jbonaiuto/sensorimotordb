from shutil import copyfile
import django
from django.contrib.auth.models import User
from django.db import connections
from neo import io, os
import scipy.io
from django.db.models import Q
from sensorimotordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, Condition, UnitRecording, ConditionVideoEvent
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
    cursor.execute('DELETE FROM %s.sensorimotordb_unit WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspobservationcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspperformancecondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_condition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
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

if __name__=='__main__':
    django.setup()
    remove_all()
    import_kraskov_data('data/kraskov/units4BODB.mat','data/kraskov/')
    sed=import_bonini_data(['data/bonini/01_PIC_F5_09022012_mot_mirror_mrgSORTED.nex',
                            'data/bonini/02_Pic_F5_10022012_mot_mirror_mrgSORTED.nex'])
