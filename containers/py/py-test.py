def main():
    name = input("What is your name? ")
    print(f"Hello, {name}!")
    
    age = input("How old are you? ")
    try:
        age = int(age)
        print(f"In 10 years, you'll be {age + 10} years old!")
    except ValueError:
        print("That's not a valid age!")

if __name__ == "__main__":
    main()
