export const CODE_TEMPLATES: Record<string, string> = {
  python: `import sys

def solve(data: str) -> str:
    # \`data\` is the raw input (all of stdin).
    # Implement your solution and return the output string.
    return ""

if __name__ == "__main__":
    sys.stdout.write(solve(sys.stdin.read()))
`,
  javascript: `function solve(data) {
    // \`data\` is the raw input (all of stdin).
    // Implement your solution and return the output string.
    return "";
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
    process.stdout.write(solve(input));
});
`,
  typescript: `function solve(data: string): string {
    // \`data\` is the raw input (all of stdin).
    // Implement your solution and return the output string.
    return "";
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk: string) => { input += chunk; });
process.stdin.on("end", () => {
    process.stdout.write(solve(input));
});
`,
  java: `import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        StringBuilder sb = new StringBuilder();
        while (sc.hasNextLine()) {
            if (sb.length() > 0) sb.append("\\n");
            sb.append(sc.nextLine());
        }
        System.out.print(solve(sb.toString()));
    }

    public static String solve(String data) {
        // \`data\` is the raw input (all of stdin).
        // Implement your solution and return the output string.
        return "";
    }
}
`,
  cpp: `#include <iostream>
#include <string>

using namespace std;

string solve(string data) {
    // \`data\` is the raw input (all of stdin).
    // Implement your solution and return the output string.
    return "";
}

int main() {
    string data, line;
    while (getline(cin, line)) {
        data += line + "\\n";
    }
    cout << solve(data);
    return 0;
}
`,
  go: `package main

import (
    "fmt"
    "io"
    "os"
)

func solve(data string) string {
    // \`data\` is the raw input (all of stdin).
    // Implement your solution and return the output string.
    return ""
}

func main() {
    b, _ := io.ReadAll(os.Stdin)
    fmt.Print(solve(string(b)))
}
`,
  rust: `use std::io::{self, Read};

fn solve(data: &str) -> String {
    // \`data\` is the raw input (all of stdin).
    // Implement your solution and return the output string.
    String::new()
}

fn main() {
    let mut data = String::new();
    io::stdin().read_to_string(&mut data).unwrap();
    print!("{}", solve(&data));
}
`,
};

export const LANGUAGE_EXTENSIONS: Record<string, string> = {
  python: "py",
  javascript: "js",
  typescript: "ts",
  java: "java",
  cpp: "cpp",
  go: "go",
  rust: "rs",
};

export const LANGUAGE_MONACO_IDS: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  java: "java",
  cpp: "cpp",
  go: "go",
  rust: "rust",
};
