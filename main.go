package main

import (
	"bytes"
	"fmt"
	"log"
	"net/smtp"
	"os"
	"os/exec"
	"strconv"
	"strings"

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

func call(cmd string, shell string) (string, string, error) {
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	out := exec.Command(shell, "-c", cmd)
	out.Stdout = &stdout
	out.Stderr = &stderr
	err := out.Run()
	return stdout.String(), stderr.String(), err
}

func sendmail(server string, port int, user string, pass string, from string, to string, subject string, message string) error {
	smtpserver := server + ":" + strconv.Itoa(port)
	body := subject + "\n\n" + message
	status := smtp.SendMail(smtpserver, smtp.PlainAuth("", user, pass, server), from, []string{to}, []byte(body))
	return status
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

func acmeTest(maindomain string, domains string, adminemail string, python string) (string, string, error) {
	var out string
	var errout string
	var err error
	dir, err := os.Getwd()
	if err != nil {
		return out, errout, err
	}
	out, errout, err = call("/usr/bin/certbot certonly --agree-to --email "+adminemail+" --expand --manual-public-ip-logging-ok --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --dry-run --manual-auth-hook '"+python+" "+dir+"/auth.pyc' --manual-cleanup-hook '"+python+" "+dir+"/clean.pyc' "+domains, "/bin/bash")
	return out, errout, err
}

func acmeRun(maindomain string, domains string, adminemail string, python string) (string, string, error) {
	var out string
	var errout string
	var err error
	dir, err := os.Getwd()
	if err != nil {
		return out, errout, err
	}
	out, errout, err = call("/usr/bin/certbot certonly --agree-to --email "+adminemail+" --expand --manual-public-ip-logging-ok --cert-name "+maindomain+" --manual --renew-by-default --preferred-challenges dns --manual-auth-hook '"+python+" "+dir+"/auth.pyc' --manual-cleanup-hook '"+python+" "+dir+"/clean.pyc' "+domains, "/bin/bash")
	return out, errout, err
}

func reloadServer(testcmd string, reloadcmd string) (string, string, error) {
	out, errout, err := call(testcmd, "/bin/bash")
	if err != nil {
		return out, errout, err
	}
	out, errout, err = call(reloadcmd, "/bin/bash")
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

func main() {
	var err error
	var stdout string
	var stderr string
	var argument string

	argument = os.Args[1]

	// Read config
	cfg, err := ini.Load("config.ini")
	if err != nil {
		fmt.Println("Error: " + err.Error())
		os.Exit(1)
	}

	// Set config
	ZONE := cfg.Section("GENERAL").Key("ZONE").Strings(",")
	ADMINEMAIL := cfg.Section("GENERAL").Key("ADMIN_EMAIL").String()
	LOGFILE := cfg.Section("GENERAL").Key("LOG_FILE").String()
	PYTHON := cfg.Section("GENERAL").Key("PYTHON").String()
	TESTCONFIG := cfg.Section("WEBSERVER").Key("TEST_CONFIG").String()
	RELOADCONFIG := cfg.Section("WEBSERVER").Key("RELOAD_CONFIG").String()
	SMTPENABLED := cfg.Section("SMTP").Key("ENABLED").MustBool()
	SMTPSERVER := cfg.Section("SMTP").Key("SERVER").String()
	SMTPPORT := cfg.Section("SMTP").Key("PORT").MustInt()
	SMTPUSER := cfg.Section("SMTP").Key("USERNAME").String()
	SMTPPASS := cfg.Section("SMTP").Key("PASSWORD").String()
	SENDER := cfg.Section("SMTP").Key("FROM").String()
	RECIPIENT := cfg.Section("SMTP").Key("TO").String()
        POSTHOOKENABLED := cfg.Section("POSTHOOK").Key("ENABLED").MustBool()
        POSTHOOKSCRIPT := cfg.Section("POSTHOOK").Key("SCRIPT").String()
	HOSTNAME, err := os.Hostname()
	/*_ = TESTCONFIG
	_ = RELOADCONFIG
	_ = SMTPENABLED
	_ = SMTPSERVER
	_ = SMTPPORT
	_ = SMTPUSER
	_ = SMTPPASS
	_ = SENDER
	_ = RECIPIENT
	_ = HOSTNAME*/
	if err != nil {
		fmt.Println("Error: " + err.Error())
		os.Exit(1)
	}

	// Set logging
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

	fmt.Println("-= LetsEncrypt NIC =-")

	exportCredentials()

	fmt.Println("Preparing a domain list...")
	maindomain := ZONE[0]
	domains := makeList(ZONE)

	fmt.Println("[+] ACME Test: [ START ]")
	log.Println("ACME Test Start")
	stdout, stderr, err = acmeTest(maindomain, domains, ADMINEMAIL, PYTHON)
	log.Println(stdout)
	if err != nil {
		fmt.Println("[-] ACME Test: [ FAILED ]: " + stderr + " " + err.Error())
		log.Println("ACME Test Failed: " + stderr + " " + err.Error())
		if SMTPENABLED {
			subject := "[" + HOSTNAME + "] ACME Test: [ FAILED ]"
			err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
			fmt.Println("SMTP server error: " + err.Error())
			log.Println("SMTP server error: " + err.Error())
		}
		os.Exit(1)
	}
	fmt.Println("[+] ACME Test: [ DONE ]")
	log.Println("ACME Test Done")
	if argument == "-t" {
		destroyCredentials()
		fmt.Println("-= Program completed! =-")
		os.Exit(0)
	}

	fmt.Println("[+] ACME Run: [ START ]")
	log.Println("ACME Run Start")
	stdout, stderr, err = acmeRun(maindomain, domains, ADMINEMAIL, PYTHON)
	log.Println(stdout)
	if err != nil {
		fmt.Println("[-] ACME Run: [ FAILED ]: " + stderr + " " + err.Error())
		log.Println("ACME Run Failed: " + stderr + " " + err.Error())
		if SMTPENABLED {
			subject := "[" + HOSTNAME + "] ACME Run: [ FAILED ]"
			err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
			fmt.Println("SMTP server error: " + err.Error())
			log.Println("SMTP server error: " + err.Error())
		}
		os.Exit(1)
	}
	fmt.Println("[+] ACME Run: [ DONE ]")
	log.Println("ACME Run Done")

	fmt.Println("[+] SERVER Reload: [ START ]")
	log.Println("SERVER Reload Start")
	stdout, stderr, err = reloadServer(TESTCONFIG, RELOADCONFIG)
	log.Println(stdout)
	if err != nil {
		fmt.Println("[-] SERVER Reload: [ FAILED ]: " + stderr + " " + err.Error())
		log.Println("SERVER Reload Failed: " + stderr + " " + err.Error())
		if SMTPENABLED {
			subject := "[" + HOSTNAME + "] SERVER Reload: [ FAILED ]"
			err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
			fmt.Println("SMTP server error: " + err.Error())
			log.Println("SMTP server error: " + err.Error())
		}
		os.Exit(1)
	}
	fmt.Println("[+] SERVER Reload: [ DONE ]")
	log.Println("SERVER Reload Done")

	destroyCredentials()

        if POSTHOOKENABLED {
		stdout, stderr, err = call(POSTHOOKSCRIPT, "/bin/bash")
		log.Println(stdout)
		if err != nil {
			fmt.Println("[-] POST HOOK Run: [ FAILED ]: " + stderr + " " + err.Error())
			log.Println("POST HOOK Run Failed: " + stderr + " " + err.Error())
			if SMTPENABLED {
                        	subject := "[" + HOSTNAME + "] SERVER Reload: [ FAILED ]"
                        	err = sendmail(SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, SENDER, RECIPIENT, subject, stderr+" "+err.Error())
                        	fmt.Println("SMTP server error: " + err.Error())
                        	log.Println("SMTP server error: " + err.Error())
                	}
			os.Exit(1)
		}
		fmt.Println("[+] POST HOOK Run: [ DONE ]")
		log.Println("POST HOOK Run Done")
	}

	fmt.Println("-= Program completed! =-")
}
