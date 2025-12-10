import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager

db = DatabaseManager()

db.add_manga(
    title='Loco Frontera',
    check_url='https://olympusbiblioteca.com/series/comic-loco-frontera-20251115-081419578',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/loco-frontera/',
    last_checked_chapter='215',
    current_chapter='215',
    current_reading='215',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Mi Evolución a Partir de un Árbol Gigante',
    check_url='https://olympusbiblioteca.com/series/comic-arbol-mamv20-225-adisimo77213124',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/mi-evolucion-a-partir-de-un-arbol-gigante/',
    last_checked_chapter='451',
    current_chapter='451',
    current_reading='451',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Como madrear',
    check_url='https://olympusbiblioteca.com/series/comic-como-madrear-20251115-081321905',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/como-madrear/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=0,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Cultivando solo en la torre',
    check_url='https://olympusbiblioteca.com/series/comic-t0w4r-nek0-53065062',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/cultivando-solo-en-la-torre/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='el Dios de la Batalla Suicida',
    check_url='https://olympusbiblioteca.com/series/comic-el-dios-de-la-batalla-suicida-20251115-080903567',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/el-dios-de-la-batalla-suicida/',
    last_checked_chapter='93',
    current_chapter='93',
    current_reading='93',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='El maestro de la espada acogedor de estrellas',
    check_url='https://olympusbiblioteca.com/series/comic-el-maestro-de-la-espada-acogedor-de-estrellas-20251115-080600431',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/el-maestro-de-la-espada-acogedor-de-estrellas/',
    last_checked_chapter='96',
    current_chapter='96',
    current_reading='96',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='El Mago Devorador de Talentos',
    check_url='https://olympusbiblioteca.com/series/comic-el-mago-20-225-devorador-de-talentos13424',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/el-mago-devorador-de-talentos/',
    last_checked_chapter='112',
    current_chapter='112',
    current_reading='112',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='El regreso del héroe de clase: Desastre',
    check_url='https://olympusbiblioteca.com/series/comic-el-cl20-225-ase-desastre13424',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/el-regreso-del-heroe-de-clase-desastre/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=0,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Nivelando Con Los Dioses',
    check_url='https://olympusbiblioteca.com/series/comic-nivel20-225-ando-con-los-dioses13424',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/nivelando-con-los-dioses/',
    last_checked_chapter='149',
    current_chapter='149',
    current_reading='149',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Solo Leveling: Ragnarok',
    check_url='https://olympusbiblioteca.com/series/comic-27-02-20-225-eling456456',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/solo-leveling-ragnarok/',
    last_checked_chapter='62',
    current_chapter='62',
    current_reading='62',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='el bully de bullies',
    check_url='https://olympusbiblioteca.com/series/comic-el-bully-de-bullies-20251115-081212047',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/el-bully-de-bullies/',
    last_checked_chapter='112',
    current_chapter='112',
    current_reading='112',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='¡Nigromante¡, ¡Yo soy la plaga!',
    check_url='https://olympusbiblioteca.com/series/comic-nigrom20-225-ante-yo-soy-la-plagaasdfasd',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/nigromante-yo-soy-la-plaga/',
    last_checked_chapter='101',
    current_chapter='101',
    current_reading='101',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Pick me up, Gacha Infinito',
    check_url='https://olympusbiblioteca.com/series/comic-pick-me-up-gacha-infinito-20251115-081640612',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/pick-me-up/',
    last_checked_chapter='174',
    current_chapter='174',
    current_reading='174',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Torre de Dios : Urek Mazino',
    check_url='https://olympusbiblioteca.com/series/comic-torre-de-dios-urek-mazino-20251115-081150481',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/torre-de-dios-urek-mazino/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=0,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Soldado Esqueleto',
    check_url='https://olympusbiblioteca.com/series/comic-soldado-esqueleto-20251115-081311323',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/soldado-esqueleto/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=0,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Shirone El Infinit0 (Mago infinito)',
    check_url='https://olympusbiblioteca.com/series/comic-shirone20-225-el22-infinit015551251524131123',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/mago-infinito/',
    last_checked_chapter='144',
    current_chapter='144',
    current_reading='144',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Regresión absoluta',
    check_url='https://olympusbiblioteca.com/series/comic-regresion-absoluta-20251115-080858466',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/regresion-absoluta/',
    last_checked_chapter='0',
    current_chapter='0',
    current_reading='0',
    tracking=0,
    olympus_index_url='',
    last_download_url=''
)

db.add_manga(
    title='Th3 Breaker Fuerza eterna ',
    check_url='https://olympusbiblioteca.com/series/comic-th3-breaker-fuerza-eterna-20251115-081538553',
    page_type_id=1,
    local_storage_path='/home/pablopi/Server/ServerManga/mangas/th3-breaker-fuerza-eterna/',
    last_checked_chapter='100',
    current_chapter='100',
    current_reading='100',
    tracking=1,
    olympus_index_url='',
    last_download_url=''
)

print("Todos los mangas agregados correctamente")