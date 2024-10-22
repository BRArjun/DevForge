package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)

	fmt.Print("What is your name? ")
	name, _ := reader.ReadString('\n')
	name = strings.TrimSpace(name)
	
	fmt.Printf("Hello, %s!\n", name)
	
	fmt.Print("How old are you? ")
	ageStr, _ := reader.ReadString('\n')
	ageStr = strings.TrimSpace(ageStr)
	
	age, err := strconv.Atoi(ageStr)
	if err != nil {
		fmt.Println("That's not a valid age!")
	} else {
		fmt.Printf("In 10 years, you'll be %d years old!\n", age+10)
	}
}
