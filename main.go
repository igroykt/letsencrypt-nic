package main

import (
	"encoding/base64"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/smtp"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	"gopkg.in/ini.v1"
)

// Configuration section

// USERNAME : NIC-D login
const USERNAME string = "XXX/NIC-D"

// PASSWORD : NIC-D password
const PASSWORD string = "XXX"

// CLIENTID : NIC Oauth client id
const CLIENTID string = "XXX"

// CLIENTSECRET : NIC Oauth client secret
const CLIENTSECRET string = "XXX"

// End of section

func sendmail(server string, port int, user string, pass string, from string, to []string, subject string, message string) error {
	smtpserver := server + ":" + strconv.Itoa(port)
	body := "Subject: " + subject + "\n\n" + message
	status := smtp.SendMail(smtpserver, smtp.PlainAuth("", user, pass, server), from, to, []byte(body))
	return status
}

// sendmailNoAuth : https://gadelkareem.com/2018/05/03/golang-send-mail-without-authentication-using-localhost-sendmail-or-postfix/
func sendmailNoAuth(server string, port int, from string, to []string, subject string, message string) error {
	addr := server + ":" + strconv.Itoa(port)

	r := strings.NewReplacer("\r\n", "", "\r", "", "\n", "", "%0a", "", "%0d", "")

	c, err := smtp.Dial(addr)
	if err != nil {
		return err
	}
	defer c.Close()

	if err = c.Mail(r.Replace(from)); err != nil {
		return err
	}

	for i := range to {
		to[i] = r.Replace(to[i])
		if err = c.Rcpt(to[i]); err != nil {
			return err
		}
	}

	w, err := c.Data()
	if err != nil {
		return err
	}

	msg := "To: " + strings.Join(to, ",") + "\r\n" +
		"From: " + from + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"Content-Type: text/plain; charset=\"UTF-8\"\r\n" +
		"Content-Transfer-Encoding: base64\r\n" +
		"\r\n" + base64.StdEncoding.EncodeToString([]byte(message))

	_, err = w.Write([]byte(msg))
	if err != nil {
		return err
	}
	err = w.Close()
	if err != nil {
		return err
	}
	return c.Quit()
}

func makeList(zone []string) string {
	var tmp []string
	for _, domain := range zone {
		domain = strings.TrimSpace(domain)
		domain = "-d " + domain
		tmp = append(tmp, domain)
	}
	data := strings.Join(tmp, " ")
	return data
}

func makeMainDomain(zone string) string {
	wildcard := strings.Count(zone, "*")
	if wildcard > 0 {
		zone = strings.Replace(zone, "*.", "", -1)
		return zone
	}
	return zone
}

func acmeTest(maindomain string, domains string, adminemail string, config_dir string, certbot string, SHELL string) (string, string, error) {
	var out string
	var errout string
	var err error
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		return out, errout, err
	}
	if runtime.GOOS == "windows" {
		out, errout, err = call(certbot+" certonly --config-dir "+config_dir+" --agree-tos --email "+adminemail+" --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --dry-run --manual-auth-hook auth.exe --manual-cleanup-hook clean.exe "+domains, SHELL)
	} else {
		out, errout, err = call(certbot+" certonly --config-dir "+config_dir+" --agree-tos --email "+adminemail+" --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --dry-run --manual-auth-hook '"+dir+"/auth' --manual-cleanup-hook '"+dir+"/clean' "+domains, SHELL)
	}
	return out, errout, err
}

func acmeRun(maindomain string, domains string, adminemail string, config_dir string, certbot string, SHELL string) (string, string, error) {
	var out string
	var errout string
	var err error
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		return out, errout, err
	}
	if runtime.GOOS == "windows" {
		out, errout, err = call(certbot+" certonly --config-dir "+config_dir+" --agree-tos --email "+adminemail+" --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --manual-auth-hook auth.exe --manual-cleanup-hook clean.exe "+domains, SHELL)
	} else {
		out, errout, err = call(certbot+" certonly --config-dir "+config_dir+" --agree-tos --email "+adminemail+" --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --manual-auth-hook '"+dir+"/auth' --manual-cleanup-hook '"+dir+"/clean' "+domains, SHELL)
	}
	return out, errout, err
}

func reloadServer(testcmd string, reloadcmd string, SHELL string) (string, string, error) {
	out, errout, err := call(testcmd, SHELL)
	if err != nil {
		return out, errout, err
	}
	out, errout, err = call(reloadcmd, SHELL)
	return out, errout, err
}

func exportCredentials() {
	os.Setenv("NICUSER", USERNAME)
	os.Setenv("NICPASS", PASSWORD)
	os.Setenv("NICID", CLIENTID)
	os.Setenv("NICSECRET", CLIENTSECRET)
}

func destroyCredentials() {
	os.Unsetenv("NICUSER")
	os.Unsetenv("NICPASS")
	os.Unsetenv("NICID")
	os.Unsetenv("NICSECRET")
}

// fileExists : https://golangcode.com/check-if-a-file-exists/
func fileExists(filename string) bool {
	info, err := os.Stat(filename)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}

func isDeactivated(lelog string) (bool, error) {
	sdate := time.Now().Format("2006-01-02")
	sline := "deactivated"
	var trigger bool
	data, err := ioutil.ReadFile(lelog)
	if err != nil {
		return false, err
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.Index(line, sdate) > -1 {
			trigger = true
		}
		if trigger && strings.Index(line, sline) > -1 {
			return true, errors.New(line)
		}
	}
	return false, nil
}

func main() {
	var err error
	var stdout string
	var stderr string
	var subject string
	var deactivated bool

	testPtr := flag.Bool("t", false, "test and exit")
	verbPtr := flag.Bool("v", false, "verbose mode")
	flag.Parse()

	// Read config
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		fmt.Println("Error: " + err.Error())
		os.Exit(1)
	}
	cfg, err := ini.Load(dir + "/config.ini")
	if err != nil {
		fmt.Println("Error: " + err.Error())
		os.Exit(1)
	}

	// Set config
	ZONE := cfg.Section("GENERAL").Key("ZONE").Strings(",")
	ADMINEMAIL := cfg.Section("GENERAL").Key("ADMIN_EMAIL").String()
	LOGFILE := "main.log"
	SHELL := cfg.Section("GENERAL").Key("OS_SHELL").String()
	CONFIG_DIR := cfg.Section("GENERAL").Key("LE_CONFIG_DIR").String()
	CERTBOT := cfg.Section("GENERAL").Key("CERTBOT").String()
	LELOG := cfg.Section("GENERAL").Key("LE_LOG").String()
	WEBSERVERENABLED := cfg.Section("WEBSERVER").Key("ENABLED").MustBool()
	TESTCONFIG := cfg.Section("WEBSERVER").Key("TEST_CONFIG").String()
	RELOADCONFIG := cfg.Section("WEBSERVER").Key("RELOAD_CONFIG").String()
	SMTPENABLED := cfg.Section("SMTP").Key("ENABLED").MustBool()
	SMTPSERVER := cfg.Section("SMTP").Key("SERVER").String()
	SMTPPORT := cfg.Section("SMTP").Key("PORT").MustInt()
	SMTPUSER := cfg.Section("SMTP").Key("USERNAME").String()
	SMTPPASS := cfg.Section("SMTP").Key("PASSWORD").String()
	SENDER := cfg.Section("SMTP").Key("FROM").String()
	RECIPIENT := cfg.Section("SMTP").Key("TO").Strings(",")
	POSTHOOKENABLED := cfg.Section("POSTHOOK").Key("ENABLED").MustBool()
	POSTHOOKSCRIPT := cfg.Section("POSTHOOK").Key("SCRIPT").String()
	HOSTNAME, err := os.Hostname()

	if err != nil {
		fmt.Println("Error: " + err.Error())
		os.Exit(1)
	}

	// Set logging
	LOGFILE = dir + "/" + LOGFILE
	if fileExists(LOGFILE) {
		out := os.Remove(LOGFILE)
		_ = out
	}
	logfile, err := os.OpenFile(LOGFILE, os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Println("Logger error: " + err.Error())
		os.Exit(1)
	}
	defer logfile.Close()
	log.SetOutput(logfile)

	if *verbPtr {
		fmt.Println("-= LetsEncrypt NIC =-")
	}
	log.Println("-= LetsEncrypt NIC =-")

	exportCredentials()

	if *verbPtr {
		fmt.Println("Preparing domain list...")
	}
	log.Println("Preparing domain list...")
	maindomain := makeMainDomain(ZONE[0])
	domains := makeList(ZONE)

	if *testPtr {
		if *verbPtr {
			fmt.Println("[+] ACME Test: [ START ]")
		}
		log.Println("ACME Test Start")
		stdout, stderr, err = acmeTest(maindomain, domains, ADMINEMAIL, CONFIG_DIR, CERTBOT, SHELL)
		log.Println(stdout)
		deactivated, err = isDeactivated(LELOG)
		if err != nil {
			if *verbPtr {
				fmt.Println("[-] ACME Test: [ FAILED ]: " + stderr + " " + err.Error())
			}
			log.Println("ACME Test Failed: " + stderr + " " + err.Error())
			if SMTPENABLED {
				if deactivated {
					subject = "[" + HOSTNAME + "] ACME Test: account deactivated"
				} else {
					subject = "[" + HOSTNAME + "] ACME Test: [ FAILED ]"
				}
				if len(SMTPUSER) > 0 && len(SMTPPASS) > 0 {
					err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				} else {
					err = sendmailNoAuth(SMTPSERVER, SMTPPORT, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				}
				if err != nil {
					if *verbPtr {
						fmt.Println("SMTP server error: " + err.Error())
					}
					log.Println("SMTP server error: " + err.Error())
				}
			}
			os.Exit(1)
		}
		if *verbPtr {
			fmt.Println("[+] ACME Test: [ DONE ]")
		}
		log.Println("ACME Test Done")
		destroyCredentials()
		if *verbPtr {
			fmt.Println("-= Program completed! =-")
		}
		log.Println("-= Program completed! =-")
		os.Exit(0)
	}

	if *verbPtr {
		fmt.Println("[+] ACME Run: [ START ]")
	}
	log.Println("ACME Run Start")
	stdout, stderr, err = acmeRun(maindomain, domains, ADMINEMAIL, CONFIG_DIR, CERTBOT, SHELL)
	log.Println(stdout)
	deactivated, err = isDeactivated(LELOG)
	if err != nil {
		if *verbPtr {
			fmt.Println("[-] ACME Run: [ FAILED ]: " + stderr + " " + err.Error())
		}
		log.Println("ACME Run Failed: " + stderr + " " + err.Error())
		if SMTPENABLED {
			if deactivated {
				subject = "[" + HOSTNAME + "] ACME Run: account deactivated"
			} else {
				subject = "[" + HOSTNAME + "] ACME Run: [ FAILED ]"
			}
			if len(SMTPUSER) > 0 && len(SMTPPASS) > 0 {
				err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
			} else {
				err = sendmailNoAuth(SMTPSERVER, SMTPPORT, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
			}
			if err != nil {
				if *verbPtr {
					fmt.Println("SMTP server error: " + err.Error())
				}
				log.Println("SMTP server error: " + err.Error())
			}
		}
		os.Exit(1)
	}
	if *verbPtr {
		fmt.Println("[+] ACME Run: [ DONE ]")
	}
	log.Println("ACME Run Done")

	if WEBSERVERENABLED {
		if *verbPtr {
			fmt.Println("[+] SERVER Reload: [ START ]")
		}
		log.Println("SERVER Reload Start")
		stdout, stderr, err = reloadServer(TESTCONFIG, RELOADCONFIG, SHELL)
		log.Println(stdout)
		if err != nil {
			if *verbPtr {
				fmt.Println("[-] SERVER Reload: [ FAILED ]: " + stderr + " " + err.Error())
			}
			log.Println("SERVER Reload Failed: " + stderr + " " + err.Error())
			if SMTPENABLED {
				subject := "[" + HOSTNAME + "] SERVER Reload: [ FAILED ]"
				if len(SMTPUSER) > 0 && len(SMTPPASS) > 0 {
					err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				} else {
					err = sendmailNoAuth(SMTPSERVER, SMTPPORT, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				}
				if err != nil {
					if *verbPtr {
						fmt.Println("SMTP server error: " + err.Error())
					}
					log.Println("SMTP server error: " + err.Error())
				}
			}
			os.Exit(1)
		}
		if *verbPtr {
			fmt.Println("[+] SERVER Reload: [ DONE ]")
		}
		log.Println("SERVER Reload Done")
	}

	destroyCredentials()

	if POSTHOOKENABLED {
		if *verbPtr {
			fmt.Println("[+] POST HOOK Run: [ START]")
		}
		stdout, stderr, err = call(POSTHOOKSCRIPT, SHELL)
		log.Println(stdout)
		if err != nil {
			if *verbPtr {
				fmt.Println("[-] POST HOOK Run: [ FAILED ]: " + stderr + " " + err.Error())
			}
			log.Println("POST HOOK Run Failed: " + stderr + " " + err.Error())
			if SMTPENABLED {
				subject := "[" + HOSTNAME + "] SERVER Reload: [ FAILED ]"
				if len(SMTPUSER) > 0 && len(SMTPPASS) > 0 {
					err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				} else {
					err = sendmailNoAuth(SMTPSERVER, SMTPPORT, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
				}
				if err != nil {
					if *verbPtr {
						fmt.Println("SMTP server error: " + err.Error())
					}
					log.Println("SMTP server error: " + err.Error())
				}
			}
			os.Exit(1)
		}
		if *verbPtr {
			fmt.Println("[+] POST HOOK Run: [ DONE ]")
		}
		log.Println("POST HOOK Run Done")
	}

	if *verbPtr {
		fmt.Println("-= Program completed! =-")
	}
	log.Println("-= Program completed! =-")
}
