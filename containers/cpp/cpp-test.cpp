#include <iostream>
#include <string>

int main() {
    std::string name;
    int age;

    std::cout << "What is your name? ";
    std::getline(std::cin, name);
    
    std::cout << "Hello, " << name << "!" << std::endl;
    
    std::cout << "How old are you? ";
    std::cin >> age;
    
    if (std::cin.fail()) {
        std::cout << "That's not a valid age!" << std::endl;
    } else {
        std::cout << "In 10 years, you'll be " << age + 10 << " years old!" << std::endl;
    }

    return 0;
}
