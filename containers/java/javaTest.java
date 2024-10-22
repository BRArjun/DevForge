import java.util.Scanner;

public class javaTest {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        System.out.print("What is your name? ");
        String name = scanner.nextLine();
        
        System.out.println("Hello, " + name + "!");
        
        System.out.print("How old are you? ");
        try {
            int age = scanner.nextInt();
            System.out.println("In 10 years, you'll be " + (age + 10) + " years old!");
        } catch (Exception e) {
            System.out.println("That's not a valid age!");
        }
        
        scanner.close();
    }
}
