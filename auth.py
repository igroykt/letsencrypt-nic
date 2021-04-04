import os
import sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import time
import logging
import dns.resolver
from tld import get_tld

script_dir = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
try:
    config.read(script_dir + "/config.ini")
except Exception as err:
    sys.exit(f"Config parse: {err}")

USERNAME = os.getenv('NICUSER')
PASSWORD = os.getenv('NICPASS')
CLIENT_ID = os.getenv('NICID')
CLIENT_SECRET = os.getenv('NICSECRET')
SERVICE_ID = config.get('GENERAL', 'SERVICE_ID')
TTL = config.get('GENERAL', 'TTL')
SLEEP = int(config.get('GENERAL', 'SLEEP'))
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
CERTBOT_VALIDATION = os.getenv('CERTBOT_VALIDATION')

LOG_FILE = script_dir + "/auth.log"
TOKEN_FILE = script_dir + "/nic_token.json"

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.ERROR, filename = LOG_FILE)

try:
    oauth_config = {
	'APP_LOGIN': CLIENT_ID,
	'APP_PASSWORD': CLIENT_SECRET
    }
except Exception as err:
    logging.error(f"oauth_config error: {err}")

try:
    api = DnsApi(oauth_config)
except Exception as err:
    logging.error(f"DnsApi error: {err}")

if not os.path.exists(TOKEN_FILE):
    open(TOKEN_FILE, 'w').close()

try:
    api.authorize(
	username = USERNAME,
	password = PASSWORD,
	token_filename = TOKEN_FILE
    )
except Exception as err:
    logging.error(f"api.authorize error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
	username = USERNAME,
	password = PASSWORD,
	token_filename = TOKEN_FILE
    )

def mainDomainTail(domain):
    domain = domain.split(".")
    domain = domain[len(domain)-2:]
    tmp = []
    for level in domain:
        if "*" not in level:
            tmp.append(level)
    domain = '.'.join(tmp)
    if domain:
        return domain
    return False

def domainTail(domain):
    domain = domain.split(".")
    domain = domain[:len(domain)-2]
    tmp = []
    for level in domain:
        if "*" not in level:
            tmp.append(level)
    domain = '.'.join(tmp)
    if domain:
        return domain
    return False

def getDnsList(main_domain):
    dns_list = []
    resolver = dns.resolver.Resolver(configure = False)
    resolver.nameservers = ['8.8.8.8']
    answers = dns.resolver.resolve(main_domain, 'NS')
    for rdata in answers:
        rdata = str(rdata)[:-1]
        dns_list.append(rdata)
    dns_list.sort()
    return dns_list

def genDnsList(dns_list):
    new_dns_list = []
    resolver = dns.resolver.Resolver(configure = False)
    for item in dns_list:
        answers = dns.resolver.resolve(item, 'A')
        for rdata in answers:
            rdata = str(rdata)
            new_dns_list.append(rdata)
    return new_dns_list

def resolveDomain(dns_list, main_domain):
    time.sleep(SLEEP)
    resolver = dns.resolver.Resolver(configure = False)
    i = 1
    dns_size = len(dns_list)
    for server in dns_list:
        resolver.nameservers = [server]
        try:
            resolver.resolve(f'_acme-challenge.{main_domain}', 'TXT')
            return True
        except dns.resolver.NXDOMAIN as err:
            if i >= dns_size:
                return False
            i += 1
            pass

# https://wiki.mozilla.org/TLD_List
tld_list = [
    "com.ac", "edu.ac", "gov.ac", "net.ac", "mil.ac", "org.ac", "nom.ad",
    "net.ae", "gov.ae", "org.ae", "mil.ae", "sch.ae", "ac.ae", "pro.ae", "name.ae",
    "gov.af", "edu.af", "net.af", "com.af",
    "com.ag", "org.ag", "net.ag", "co.ag", "nom.ag",
    "off.ai", "com.ai", "net.ai", "org.ai",
    "gov.al", "edu.al", "org.al", "com.al", "net.al", "uniti.al", "tirana.al", "soros.al", "upt.al", "inima.al",
    "com.an", "net.an", "org.an", "edu.an",
    "co.ao", "ed.ao", "gv.ao", "it.ao", "og.ao", "pb.ao",
    "com.ar", "gov.ar", "int.ar", "mil.ar", "net.ar", "org.ar",
    "gv.at", "ac.at", "co.at", "or.at", "priv.at",
    "asn.au", "com.au", "net.au", "id.au", "org.au", "csiro.au", "oz.au", "info.au", "conf.au", "act.au", "nsw.au", "nt.au", "qld.au", "sa.au", "tas.au", "vic.au", "wa.au", "gov.au", "edu.au",
    "com.aw",
    "com.az", "net.az", "int.az", "gov.az", "biz.az", "org.az", "edu.az", "mil.az", "pp.az", "name.az", "info.az",
    "com.bb", "edu.bb", "gov.bb", "net.bb", "org.bb",
    "com.bd", "edu.bd", "net.bd", "gov.bd", "org.bd", "mil.bd",
    "ac.be",
    "gov.bf",
    "com.bm", "edu.bm", "org.bm", "gov.bm", "net.bm",
    "com.bn", "edu.bn", "org.bn", "net.bn",
    "com.bo", "org.bo", "net.bo", "gov.bo", "gob.bo", "edu.bo", "tv.bo", "mil.bo", "int.bo",
    "agr.br", "am.br", "art.br", "edu.br", "com.br", "coop.br", "esp.br", "far.br", "fm.br", "g12.br", "gov.br", "imb.br", "ind.br", "inf.br", "mil.br", "net.br", "org.br", "psi.br", "rec.br", "srv.br", "tmp.br", "tur.br", "tv.br", "etc.br",
    "adm.br", "adv.br", "arq.br", "ato.br", "bio.br", "bmd.br", "cim.br", "cng.br", "cnt.br", "ecn.br", "eng.br", "eti.br", "fnd.br", "fot.br", "fst.br", "ggf.br", "jor.br", "lel.br", "mat.br", "med.br", "mus.br", "not.br", "ntr.br", "odo.br",
    "ppg.br", "pro.br", "psc.br", "qsl.br", "slg.br", "trd.br", "vet.br", "zlg.br", "dpn.br", "nom.br",
    "com.bs", "net.bs", "org.bs",
    "com.bt", "edu.bt", "gov.bt", "net.bt", "org.bt",
    "co.bw", "org.bw",
    "gov.by", "mil.by",
    "ab.ca", "bc.ca", "mb.ca", "nb.ca", "nf.ca", "nl.ca", "ns.ca", "nt.ca", "nu.ca", "on.ca", "pe.ca", "qc.ca", "sk.ca", "yk.ca",
    "co.cc",
    "com.cd", "net.cd", "org.cd",
    "com.ch", "net.ch", "org.ch", "gov.ch",
    "co.ck",
    "ac.cn", "com.cn", "edu.cn", "gov.cn", "net.cn", "org.cn", "ah.cn", "bj.cn", "cq.cn", "fj.cn", "gd.cn", "gs.cn", "gz.cn", "gx.cn", "ha.cn", "hb.cn", "he.cn", "hi.cn", "hl.cn", "hn.cn", "jl.cn", "js.cn", "jx.cn", "ln.cn",
    "nm.cn", "nx.cn", "qh.cn", "sc.cn", "sd.cn", "sh.cn", "sn.cn", "sx.cn", "tj.cn", "xj.cn", "xz.cn", "yn.cn", "zj.cn",
    "com.co", "edu.co", "org.co", "gov.co", "mil.co", "net.co", "nom.co",
    "us.com",
    "ac.cr", "co.cr", "ed.cr", "fi.cr", "go.cr", "or.cr", "sa.cr",
    "com.cu", "edu.cu", "org.cu", "net.cu", "gov.cu", "inf.cu",
    "gov.cx",
    "com.cy", "biz.cy", "info.cy", "ltd.cy", "pro.cy", "net.cy", "org.cy", "name.cy", "tm.cy", "ac.cy", "ekloges.cy", "press.cy", "parliament.cy",
    "com.dm", "net.dm", "org.dm", "edu.dm", "gov.dm",
    "edu.do", "gov.do", "gob.do", "com.do", "org.do", "sld.do", "web.do", "net.do", "mil.do", "art.do",
    "com.dz", "org.dz", "net.dz", "gov.dz", "edu.dz", "asso.dz", "pol.dz", "art.dz",
    "com.ec", "info.ec", "net.ec", "fin.ec", "med.ec", "pro.ec", "org.ec", "edu.ec", "gov.ec", "mil.ec",
    "com.ee", "org.ee", "fie.ee", "pri.ee",
    "eun.eg", "edu.eg", "sci.eg", "gov.eg", "com.eg", "org.eg", "net.eg", "mil.eg",
    "com.es", "nom.es", "org.es", "gob.es", "edu.es",
    "com.et", "gov.et", "org.et", "edu.et", "net.et", "biz.et", "name.et", "info.et",
    "aland.fi",
    "biz.fj", "com.fj", "info.fj", "name.fj", "net.fj", "org.fj", "pro.fj", "ac.fj", "gov.fj", "mil.fj", "school.fj",
    "co.fk", "org.fk", "gov.fk", "ac.fk", "nom.fk", "net.fk",
    "tm.fr", "asso.fr", "nom.fr", "prd.fr", "presse.fr", "com.fr", "gouv.fr",
    "com.ge", "edu.ge", "gov.ge", "org.ge", "mil.ge", "net.ge", "pvt.ge",
    "co.gg", "net.gg", "org.gg",
    "com.gh", "edu.gh", "gov.gh", "org.gh", "mil.gh",
    "com.gi", "ltd.gi", "gov.gi", "mod.gi", "edu.gi", "org.gi",
    "com.gn", "ac.gn", "gov.gn", "org.gn", "net.gn",
    "com.gp", "net.gp", "edu.gp", "asso.gp", "org.gp",
    "com.gr", "edu.gr", "net.gr", "org.gr", "gov.gr",
    "com.hk", "edu.hk", "gov.hk", "idv.hk", "net.hk", "org.hk",
    "com.hn", "edu.hn", "org.hn", "net.hn", "mil.hn", "gob.hn",
    "iz.hr", "from.hr", "name.hr", "com.hr",
    "com.ht", "net.ht", "firm.ht", "shop.ht", "info.ht", "pro.ht", "adult.ht", "org.ht", "art.ht", "pol.ht", "rel.ht", "asso.ht", "perso.ht", "coop.ht", "med.ht", "edu.ht", "gouv.ht",
    "co.hu", "info.hu", "org.hu", "priv.hu", "sport.hu", "tm.hu", "2000.hu", "agrar.hu", "bolt.hu", "casino.hu", "city.hu", "erotica.hu", "erotika.hu", "film.hu", "forum.hu", "games.hu", "hotel.hu", "ingatlan.hu",
    "jogasz.hu", "konyvelo.hu", "lakas.hu", "media.hu", "news.hu", "reklam.hu", "sex.hu", "shop.hu", "suli.hu", "szex.hu", "tozsde.hu", "utazas.hu", "video.hu",
    "ac.id", "co.id", "or.id", "go.id",
    "gov.ie",
    "ac.il", "co.il", "org.il", "net.il", "k12.il", "gov.il", "muni.il", "idf.il",
    "co.im", "ltd.co.im", "plc.co.im", "net.im", "gov.im", "org.im", "nic.im", "ac.im",
    "co.in", "firm.in", "net.in", "org.in", "gen.in", "ind.in", "nic.in", "ac.in", "edu.in", "res.in", "gov.in", "mil.in",
    "ac.ir", "co.ir", "gov.ir", "net.ir", "org.ir", "sch.ir",
    "gov.it",
    "co.je", "net.je", "org.je",
    "edu.jm", "gov.jm", "com.jm", "net.jm", "org.jm",
    "com.jo", "org.jo", "net.jo", "edu.jo", "gov.jo", "mil.jo",
    "ac.jp", "ad.jp", "co.jp", "ed.jp", "go.jp", "gr.jp", "lg.jp", "ne.jp", "or.jp",
    "hokkaido.jp", "aomori.jp", "iwate.jp", "miyagi.jp", "akita.jp", "yamagata.jp", "fukushima.jp", "ibaraki.jp", "tochigi.jp", "gunma.jp", "saitama.jp", "chiba.jp", "tokyo.jp", "kanagawa.jp",
    "niigata.jp", "toyama.jp", "ishikawa.jp", "fukui.jp", "yamanashi.jp", "nagano.jp", "gifu.jp", "shizuoka.jp", "aichi.jp", "mie.jp", "shiga.jp", "kyoto.jp", "osaka.jp", "hyogo.jp", "nara.jp", "wakayama.jp", "tottori.jp",
    "shimane.jp", "okayama.jp", "hiroshima.jp", "yamaguchi.jp", "tokushima.jp", "kagawa.jp", "ehime.jp", "kochi.jp", "fukuoka.jp", "saga.jp", "nagasaki.jp", "kumamoto.jp", "oita.jp", "miyazaki.jp",
    "kagoshima.jp", "okinawa.jp", "sapporo.jp", "sendai.jp", "yokohama.jp", "kawasaki.jp", "nagoya.jp", "kobe.jp", "kitakyushu.jp",
    "per.kh", "com.kh", "edu.kh", "gov.kh", "mil.kh", "net.kh", "org.kh",
    "co.kr", "or.kr",
    "com.kw", "edu.kw", "gov.kw", "net.kw", "org.kw", "mil.kw",
    "edu.ky", "gov.ky", "com.ky", "org.ky", "net.ky",
    "org.kz", "edu.kz", "net.kz", "gov.kz", "mil.kz", "com.kz",
    "net.lb", "org.lb", "gov.lb", "edu.lb", "com.lb",
    "com.lc", "org.lc", "edu.lc", "gov.lc",
    "com.li", "net.li", "org.li", "gov.li",
    "gov.lk", "sch.lk", "net.lk", "int.lk", "com.lk", "org.lk", "edu.lk", "ngo.lk", "soc.lk", "web.lk", "ltd.lk", "assn.lk", "grp.lk", "hotel.lk",
    "com.lr", "edu.lr", "gov.lr", "org.lr", "net.lr",
    "org.ls", "co.ls",
    "gov.lt", "mil.lt",
    "gov.lu", "mil.lu", "org.lu", "net.lu",
    "com.lv", "edu.lv", "gov.lv", "org.lv", "mil.lv", "id.lv", "net.lv", "asn.lv", "conf.lv",
    "com.ly", "net.ly", "gov.ly", "plc.ly", "edu.ly", "sch.ly", "med.ly", "org.ly", "id.ly",
    "co.ma", "net.ma", "gov.ma", "org.ma",
    "tm.mc", "asso.mc",
    "org.mg", "nom.mg", "gov.mg", "prd.mg", "tm.mg", "com.mg", "edu.mg", "mil.mg",
    "army.mil", "navy.mil",
    "com.mk", "org.mk",
    "com.mo", "net.mo", "org.mo", "edu.mo", "gov.mo",
    "weather.mobi", "music.mobi",
    "org.mt", "com.mt", "gov.mt", "edu.mt", "net.mt",
    "com.mu", "co.mu",
    "aero.mv", "biz.mv", "com.mv", "coop.mv", "edu.mv", "gov.mv", "info.mv", "int.mv", "mil.mv", "museum.mv", "name.mv", "net.mv", "org.mv", "pro.mv",
    "ac.mw", "co.mw", "com.mw", "coop.mw", "edu.mw", "gov.mw", "int.mw", "museum.mw", "net.mw", "org.mw",
    "com.mx", "net.mx", "org.mx", "edu.mx", "gob.mx",
    "com.my", "net.my", "org.my", "gov.my", "edu.my", "mil.my", "name.my",
    "edu.ng", "com.ng", "gov.ng", "org.ng", "net.ng",
    "gob.ni", "com.ni", "edu.ni", "org.ni", "nom.ni", "net.ni",
    "000.nl", "999.nl",
    "mil.no", "stat.no", "kommune.no", "herad.no", "priv.no", "vgs.no", "fhs.no", "museum.no", "fylkesbibl.no", "folkebibl.no", "idrett.no", "geo.no", "gs.county.no", "county.no",
    "com.np", "org.np", "edu.np", "net.np", "gov.np", "mil.np",
    "gov.nr", "edu.nr", "biz.nr", "info.nr", "org.nr", "com.nr", "net.nr",
    "ac.nz", "co.nz", "cri.nz", "gen.nz", "geek.nz", "govt.nz", "iwi.nz", "maori.nz", "mil.nz", "net.nz", "org.nz", "school.nz",
    "com.om", "co.om", "edu.om", "ac.com", "sch.om", "gov.om", "net.om", "org.om", "mil.om", "museum.om", "biz.om", "pro.om", "med.om",
    "com.pa", "ac.pa", "sld.pa", "gob.pa", "edu.pa", "org.pa", "net.pa", "abo.pa", "ing.pa", "med.pa", "nom.pa",
    "com.pe", "org.pe", "net.pe", "edu.pe", "mil.pe", "gob.pe", "nom.pe",
    "com.pf", "org.pf", "edu.pf",
    "com.pg", "net.pg",
    "com.ph", "gov.ph",
    "com.pk", "net.pk", "edu.pk", "org.pk", "fam.pk", "biz.pk", "web.pk", "gov.pk", "gob.pk", "gok.pk", "gon.pk", "gop.pk", "gos.pk",
    "com.pl", "biz.pl", "net.pl", "art.pl", "edu.pl", "org.pl", "ngo.pl", "gov.pl", "info.pl", "mil.pl",
    "waw.pl", "warszawa.pl", "wroc.pl", "wroclaw.pl", "krakow.pl", "poznan.pl", "lodz.pl", "gda.pl", "gdansk.pl", "slupsk.pl", "szczecin.pl", "lublin.pl", "bialystok.pl", "olsztyn.pl", "torun.pl",
    "biz.pr", "com.pr", "edu.pr", "gov.pr", "info.pr", "isla.pr", "name.pr", "net.pr", "org.pr", "pro.pr",
    "law.pro", "med.pro", "cpa.pro",
    "edu.ps", "gov.ps", "sec.ps", "plo.ps", "com.ps", "org.ps", "net.ps",
    "com.pt", "edu.pt", "gov.pt", "int.pt", "net.pt", "nome.pt", "org.pt", "publ.pt",
    "net.py", "org.py", "gov.py", "edu.py", "com.py",
    "com.ro", "org.ro", "tm.ro", "nt.ro", "nom.ro", "info.ro", "rec.ro", "arts.ro", "firm.ro", "store.ro", "www.ro",
    "com.ru", "net.ru", "org.ru", "pp.ru", "msk.ru", "int.ru", "ac.ru",
    "gov.rw", "net.rw", "edu.rw", "ac.rw", "com.rw", "co.rw", "int.rw", "mil.rw", "gouv.rw",
    "com.sa", "edu.sa", "sch.sa", "med.sa", "gov.sa", "net.sa", "org.sa", "pub.sa",
    "com.sb", "gov.sb", "net.sb", "edu.sb",
    "com.sc", "gov.sc", "net.sc", "org.sc", "edu.sc",
    "com.sd", "net.sd", "org.sd", "edu.sd", "med.sd", "tv.sd", "gov.sd", "info.sd",
    "org.se", "pp.se", "tm.se", "brand.se", "parti.se", "press.se", "komforb.se", "kommunalforbund.se", "komvux.se", "lanarb.se", "lanbib.se", "naturbruksgymn.se", "sshn.se", "fhv.se", "fhsk.se", "fh.se", "mil.se",
    "ab.se", "c.se", "d.se", "e.se", "f.se", "g.se", "h.se", "i.se", "k.se", "m.se", "n.se", "o.se", "s.se", "t.se", "u.se", "w.se", "x.se", "y.se", "z.se", "ac.se", "bd.se",
    "com.sg", "net.sg", "org.sg", "gov.sg", "edu.sg", "per.sg", "idn.sg",
    "edu.sv", "com.sv", "gob.sv", "org.sv", "red.sv",
    "gov.sy", "com.sy", "net.sy",
    "ac.th", "co.th", "in.th", "go.th", "mi.th", "or.th", "net.th",
    "ac.tj", "biz.tj", "com.tj", "co.tj", "edu.tj", "int.tj", "name.tj", "net.tj", "org.tj", "web.tj", "gov.tj", "go.tj", "mil.tj",
    "com.tn", "intl.tn", "gov.tn", "org.tn", "ind.tn", "nat.tn", "tourism.tn", "info.tn", "ens.tn", "fin.tn", "net.tn",
    "gov.to",
    "gov.tp",
    "com.tr", "info.tr", "biz.tr", "net.tr", "org.tr", "web.tr", "gen.tr", "av.tr", "dr.tr", "bbs.tr", "name.tr", "tel.tr", "gov.tr", "bel.tr", "pol.tr", "mil.tr", "k12.tr", "edu.tr",
    "co.tt", "com.tt", "org.tt", "net.tt", "biz.tt", "info.tt", "pro.tt", "name.tt", "edu.tt", "gov.tt",
    "gov.tv",
    "edu.tw", "gov.tw", "mil.tw", "com.tw", "net.tw", "org.tw", "idv.tw", "game.tw", "ebiz.tw", "club.tw", "網路.tw", "組織.tw", "商業.tw",
    "co.tz", "ac.tz", "go.tz", "or.tz", "ne.tz",
    "com.ua", "gov.ua", "net.ua", "edu.ua", "org.ua",
    "cherkassy.ua", "ck.ua", "chernigov.ua", "cn.ua", "chernovtsy.ua", "cv.ua", "crimea.ua", "dnepropetrovsk.ua", "dp.ua", "donetsk.ua", "dn.ua", "ivano-frankivsk.ua",
    "if.ua", "kharkov.ua", "kh.ua", "kherson.ua", "ks.ua", "khmelnitskiy.ua", "km.ua", "kiev.ua", "kv.ua", "kirovograd.ua", "kr.ua", "lugansk.ua", "lg.ua", "lutsk.ua", "lviv.ua", "nikolaev.ua", "mk.ua",
    "odessa.ua", "od.ua", "poltava.ua", "pl.ua", "rovno.ua", "rv.ua", "sebastopol.ua", "sumy.ua", "ternopil.ua", "te.ua", "uzhgorod.ua", "vinnica.ua", "vn.ua", "zaporizhzhe.ua", "zp.ua", "zhitomir.ua", "zt.ua",
    "co.ug", "ac.ug", "sc.ug", "go.ug", "ne.ug", "or.ug",
    "ac.uk", "co.uk", "gov.uk", "ltd.uk", "me.uk", "mil.uk", "mod.uk", "net.uk", "nic.uk", "nhs.uk", "org.uk", "plc.uk", "police.uk", "sch.uk", "bl.uk", "british-library.uk", "icnet.uk", "jet.uk",
    "nel.uk", "nls.uk", "national-library-scotland.uk", "parliament.uk",
    "ak.us", "al.us", "ar.us", "az.us", "ca.us", "co.us", "ct.us", "dc.us", "de.us", "dni.us", "fed.us", "fl.us", "ga.us", "hi.us", "ia.us", "id.us", "il.us", "in.us", "isa.us", "kids.us", "ks.us", "ky.us", "la.us", "ma.us", "md.us",
    "me.us", "mi.us", "mn.us", "mo.us", "ms.us", "mt.us", "nc.us", "nd.us", "ne.us", "nh.us", "nj.us", "nm.us", "nsn.us", "nv.us", "ny.us", "oh.us", "ok.us", "or.us", "pa.us", "ri.us", "sc.us", "sd.us", "tn.us", "tx.us",
    "ut.us", "vt.us", "va.us", "wa.us", "wi.us", "wv.us", "wy.us",
    "edu.uy", "gub.uy", "org.uy", "com.uy", "net.uy", "mil.uy",
    "vatican.va",
    "com.ve", "net.ve", "org.ve", "info.ve", "co.ve", "web.ve",
    "com.vi", "org.vi", "edu.vi", "gov.vi",
    "com.vn", "net.vn", "org.vn", "edu.vn", "gov.vn", "int.vn", "ac.vn", "biz.vn", "info.vn", "name.vn", "pro.vn", "health.vn",
    "com.ye", "net.ye",
    "ac.yu", "co.yu", "org.yu", "edu.yu",
    "ac.za", "city.za", "co.za", "edu.za", "gov.za", "law.za", "mil.za", "nom.za", "org.za", "school.za", "alt.za", "net.za", "ngo.za", "tm.za", "web.za",
    "co.zm", "org.zm", "gov.zm", "sch.zm", "ac.zm",
    "co.zw", "org.zw", "gov.zw", "ac.zw"
]

def is_tld():
    domain = get_tld(CERTBOT_DOMAIN, fix_protocol=True)
    if any(domain in s for s in tld_list):
        return True
    return False

domain_object = get_tld(CERTBOT_DOMAIN, fix_protocol=True, as_object=True)
tld = is_tld()

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        if tld:
            domain_tail = domain_object.subdomain.split(".")
            domain_tail = domain_tail[1:]
            domain_tail = '.'.join(domain_tail)
            record = TXTRecord(name = f"_acme-challenge.{domain_tail}", txt = CERTBOT_VALIDATION, ttl = TTL)
        else:
            domain_tail = domainTail(CERTBOT_DOMAIN)
            record = TXTRecord(name = f"_acme-challenge.{domain_tail}", txt = CERTBOT_VALIDATION, ttl = TTL)
    else:
        record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)
except Exception as err:
    logging.error(f"TXTRecord error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
        username = USERNAME,
        password = PASSWORD,
        token_filename = TOKEN_FILE
    )
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        if tld:
            domain_tail = domain_object.subdomain.split(".")
            domain_tail = domain_tail[1:]
            domain_tail = '.'.join(domain_tail)
            record = TXTRecord(name = f"_acme-challenge.{domain_tail}", txt = CERTBOT_VALIDATION, ttl = TTL)
        else:
            domain_tail = domainTail(CERTBOT_DOMAIN)
            record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)
    else:
        record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        main_domain = mainDomainTail(CERTBOT_DOMAIN)
        api.add_record(record, SERVICE_ID, main_domain)
    else:
        api.add_record(record, SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.add_record error: {err}")

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        main_domain = mainDomainTail(CERTBOT_DOMAIN)
        api.commit(SERVICE_ID, main_domain)
    else:
        api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.commit error: {err}")

if len(CERTBOT_DOMAIN.split(".")) > 2:
    main_domain = mainDomainTail(CERTBOT_DOMAIN)
else:
    main_domain = CERTBOT_DOMAIN

dns_list = getDnsList(main_domain)
dns_ip_list = genDnsList(dns_list)
is_resolved = resolveDomain(dns_ip_list, main_domain)
if not is_resolved:
    logging.error(f"resolver.resolve error: Could not find validation TXT record for {CERTBOT_DOMAIN}")
    raise Exception(f"resolver.resolve error: Could not find validation TXT record {CERTBOT_DOMAIN}")