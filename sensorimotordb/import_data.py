import datetime
from decimal import Decimal
from shutil import copyfile
import django
from django.contrib.auth.models import User
from django.db import connections
from haystack.management.commands import rebuild_index
from neo import io, os
import scipy.io
from glob import glob
from django.db.models import Q
from sensorimotordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, \
    Species, GraspPerformanceCondition, Condition, UnitRecording, ConditionVideoEvent, Penetration, Subject, Session
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
    cursor.execute('DELETE FROM %s.sensorimotordb_unit WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspobservationcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspperformancecondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_graspcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_conditionvideoevent WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_condition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_session WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.sensorimotordb_subject WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    for exp in Experiment.objects.using(db).all():
        cursor.execute('DELETE FROM %s.sensorimotordb_experiment WHERE id=%d' % (settings.DATABASES[db]['NAME'],exp.id))
    cursor.close()

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


def import_social_goal_mirror_restricted_data(db='default'):
    monkeys = ['Betta', 'Houdini']
    monkey_pentrations={
        'Betta': [2, 8, 10, 12, 22],
        'Houdini': [15, 19, 20, 23, 27, 38, 39]
    }
    collator = User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='jbonaiuto').count():
        collator = User.objects.using(db).get(username='jbonaiuto')

    exp_title = 'F5 mirror neuron - Social goals (restricted penetrations)'
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

        penetrations=monkey_pentrations[monkey]
        session_num=1

        for pen_num in penetrations:
            penetration_dir = '/home/bonaiuto/Dropbox/social_goal_mirror/data/%s%02d' % (monkey, pen_num)
            penetration_label='%2d' % pen_num
            print(penetration_label)
            penetration = Penetration(label=penetration_label, subject=subject)
            penetration.save(using=db)

            session = Session(experiment=exp, session_number=session_num,
                              datetime=datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(penetration_dir,'spikes.mat'))))
            session.save()
            session_num = session_num + 1

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
                    trial.session=session
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
                    trial.session=session
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
                    trial.session=session
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
                    trial.session=session
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


def import_social_goal_mirror_all_data(db='default'):
    monkeys = ['Betta', 'Houdini']
    monkey_pentrations={
        'Betta': [2, 6, 8, 9, 10, 11, 12, 13, 15, 18, 21, 22, 37],
        'Houdini': [12, 13, 15, 19, 20, 23, 26, 27, 38, 39]
    }
    collator = User.objects.using(db).filter(is_superuser=True)[0]
    if User.objects.using(db).filter(username='jbonaiuto').count():
        collator = User.objects.using(db).get(username='jbonaiuto')

    exp_title = 'F5 mirror neuron - Social goals (all penetrations)'
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

        session_num=1

        penetrations = monkey_pentrations[monkey]
        for pen_num in penetrations:
            penetration_dir = '/home/bonaiuto/Dropbox/social_goal_mirror/data/%s%02d' % (monkey, pen_num)
            penetration_label = '%2d' % pen_num
            print(penetration_label)
            penetration = Penetration(label=penetration_label, subject=subject)
            penetration.save(using=db)

            session = Session(experiment=exp, session_number=session_num,
                              datetime=datetime.datetime.fromtimestamp(
                                  os.path.getctime(os.path.join(penetration_dir, 'spikes.mat'))))
            session.save()
            session_num = session_num + 1

            mat_file = scipy.io.loadmat(os.path.join(penetration_dir, 'spikes.mat'))

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
                    trial.session=session
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
                    trial.session=session
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
                    trial.session=session
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
                    trial.session=session
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



def import_social_goal_motor_data(db='default'):
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

    exp_title='F5 motor neurons - Social goals'
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

        nex_files=glob('/home/bonaiuto/Projects/sensorimotordb/data/ferrari/%s*.nex' % monkey)
        session_num=1
        for nex_idx, nex_file in enumerate(nex_files):

            (path,file)=os.path.split(nex_file)
            (file,ext)=os.path.splitext(file)
            penetration_label=file.split('_')[1][3:]
            penetration=Penetration(label=penetration_label, subject=subject)
            penetration.save(using=db)

            session = Session(experiment=exp, session_number=session_num,
                              datetime=datetime.datetime.fromtimestamp(os.path.getctime(nex_file)))
            session.save()
            session_num=session_num+1

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
                            trial.session=session
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
#    import_kraskov_data('data/kraskov/units4BODB.mat','data/kraskov/')
#    sed=import_bonini_data(['data/bonini/01_PIC_F5_09022012_mot_mirror_mrgSORTED.nex',
#                            'data/bonini/02_Pic_F5_10022012_mot_mirror_mrgSORTED.nex'])
    import_social_goal_motor_data()
    #import_social_goal_mirror_data()

    try:
        rebuild_index.Command().handle(interactive=False)
    except:
        pass
