# Norman Board — Tangible Programming Interface for Children

**A physical-to-code system that converts arrangements of tangible programming blocks into executable Python.**

## Overview

Norman Board explores how children can learn programming concepts through physical interaction instead of relying exclusively on a conventional screen-based code editor. Learners arrange tangible programming blocks on a board; the system recognizes the arrangement, interprets its logic and generates executable Python code.

Developed for the **Human Computer Interaction** course at American International University-Bangladesh.

## How it works

```text
Arrange physical programming blocks
    |
Camera captures the board
    |
ArUco marker detection
    |
Interpret block arrangement
    |
Custom parser
    |
Executable Python code
```

## Key features

- A tangible interface for assembling programming logic
- Computer vision-based recognition using ArUco markers
- Custom parsing logic to translate physical arrangements into code
- Python code generation and execution
- A child-oriented interaction design that connects physical actions to computational concepts

## Technologies

- Python
- Computer vision and ArUco markers
- Custom parsing and code generation
- Tangible user interface design

## Getting started

Prepare the physical board and markers used by the project, along with a compatible camera and Python environment. Configure the marker-to-instruction mapping and camera settings according to the implementation. Test recognition with a small arrangement of blocks, inspect the generated code and run it in an appropriate controlled environment.

## Design focus

The project brings together human–computer interaction, computer vision and language processing. Its central contribution is the end-to-end translation from a physical arrangement into executable logic, making programming a hands-on activity. The system is a prototype; formal learning-outcome or usability results are not claimed here.

## Project links

- [Project overview and demonstration](https://morsalin-antor-portfolio.vercel.app/project_info.html?name=norman_board)
- [GitHub profile](https://github.com/antor-morsalin)
