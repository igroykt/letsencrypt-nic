// +build win

package main

import (
	"bytes"
	"os/exec"
)

func call(cmd string, shell string) (string, string, error) {
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	out := exec.Command(shell, "/C", cmd)
	out.Stdout = &stdout
	out.Stderr = &stderr
	err := out.Run()
	return stdout.String(), stderr.String(), err
}
