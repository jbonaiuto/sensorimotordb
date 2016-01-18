from django.core.management import BaseCommand
import os
from mirrordb.import_data import import_kraskov_data, import_bonini_data, remove_all
from uscbp import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        remove_all()
        import_kraskov_data(os.path.join(settings.PROJECT_PATH,'data/kraskov/units4BODB.mat'),
            os.path.join(settings.PROJECT_PATH,'data/kraskov/'))
        sed=import_bonini_data([os.path.join(settings.PROJECT_PATH,'data/bonini/01_PIC_F5_09022012_mot_mirror_mrgSORTED.nex'),
                                os.path.join(settings.PROJECT_PATH,'data/bonini/02_Pic_F5_10022012_mot_mirror_mrgSORTED.nex')])
