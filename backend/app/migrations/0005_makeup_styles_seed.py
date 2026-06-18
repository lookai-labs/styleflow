from django.db import migrations


MAKEUP_STYLES = [
    # 여성 봄웜
    {'style_code': 'mk-sp-coral',   'style_name': '코랄 메이크업'},
    {'style_code': 'mk-sp-peach',   'style_name': '피치 메이크업'},
    {'style_code': 'mk-sp-juicy',   'style_name': '주시 메이크업'},
    # 여성 여름쿨
    {'style_code': 'mk-su-dewy',    'style_name': '듀이 메이크업'},
    {'style_code': 'mk-su-natural', 'style_name': '내추럴 메이크업'},
    {'style_code': 'mk-su-rose',    'style_name': '로즈 메이크업'},
    # 여성 가을웜
    {'style_code': 'mk-au-brown',   'style_name': '브라운 메이크업'},
    {'style_code': 'mk-au-chic',    'style_name': '시크 메이크업'},
    {'style_code': 'mk-au-office',  'style_name': '오피스 메이크업'},
    # 여성 겨울쿨
    {'style_code': 'mk-wi-burgundy', 'style_name': '버건디 메이크업'},
    {'style_code': 'mk-wi-glam',    'style_name': '글램 메이크업'},
    {'style_code': 'mk-wi-red',     'style_name': '레드 메이크업'},
    # 남성
    {'style_code': 'mk-m-sp-natural', 'style_name': '봄웜 내추럴 메이크업'},
    {'style_code': 'mk-m-su-clean',   'style_name': '여름쿨 클린 메이크업'},
    {'style_code': 'mk-m-au-soft',    'style_name': '가을웜 소프트 메이크업'},
    {'style_code': 'mk-m-wi-sharp',   'style_name': '겨울쿨 샤프 메이크업'},
]


def seed_makeup_styles(apps, schema_editor):
    MakeupStyle = apps.get_model('app', 'MakeupStyle')
    for item in MAKEUP_STYLES:
        obj, created = MakeupStyle.objects.get_or_create(
            style_code=item['style_code'],
            defaults={'style_name': item['style_name']},
        )
        if not created and obj.style_name != item['style_name']:
            obj.style_name = item['style_name']
            obj.save()


def unseed_makeup_styles(apps, schema_editor):
    MakeupStyle = apps.get_model('app', 'MakeupStyle')
    codes = [item['style_code'] for item in MAKEUP_STYLES]
    MakeupStyle.objects.filter(style_code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_makupstyle_style_code'),
    ]

    operations = [
        migrations.RunPython(seed_makeup_styles, reverse_code=unseed_makeup_styles),
    ]
