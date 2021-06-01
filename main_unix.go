// +build !win

package main

import (
	"bytes"
	"os/exec"
	"syscall"
)

func call(cmd string, shell string) (string, string, error) {
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	out := exec.Command(shell, "-c", cmd)
	out.Stdout = &stdout
	out.Stderr = &stderr
	out.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
	}
	err := out.Run()
	return stdout.String(), stderr.String(), err
}
