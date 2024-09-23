# README.md

## Project Title: Movie & TV Show Tracker

#### Video Demo:  https://youtu.be/kWMm8v3nmts

### Description
The **Movie & TV Show Tracker** is a dynamic web application designed for users to manage their viewing experiences of movies and TV shows. Utilizing the TMDB API, the app allows users to browse, rate, and keep track of what they have watched, are currently watching, or plan to watch. The project aims to provide a user-friendly interface while integrating various functionalities, such as user authentication, session management, and data storage using SQL.

### Features
- **User Authentication**: Users can sign up and log in to their accounts to manage their viewing lists.
- **Browse Movies and TV Shows**: Users can view top-rated movies and popular TV shows with detailed information.
- **Rating System**: Users can rate each show and movie they have watched, with a scale from 1 to 10.
- **Status Tracking**: Users can mark their watching status, including options like "Watching," "Completed," "On-Hold," "Dropped," and "Plan to Watch."
- **Episode Selection**: For TV shows, users can select specific seasons and episodes to manage their viewing lists.

### File Structure
├── app.py
├── requirements.txt
├── templates/
│   ├── layout.html
│   ├── signup.html
│   ├── login.html
│   ├── index.html
│   ├── movie_info.html
│   └── tv_info.html
└── static/
    └── styles.css

### File Descriptions

- **app.py**: The main application file, which contains all the routes and logic for handling requests. It manages user authentication, interacts with the TMDB API, and handles database operations.

- **requirements.txt**: Lists all the Python dependencies required to run the project. This includes libraries such as Flask, SQLAlchemy, and requests, which facilitate web development and database management.

- **templates**: This directory contains all HTML files for rendering the user interface.
  - **layout.html**: The base template that includes common elements like the header, footer, and navigation. Other templates extend this layout.
  - **signup.html**: A form for user registration. It captures username and password details.
  - **login.html**: A form for user login. It allows existing users to authenticate themselves.
  - **index.html**: The homepage that displays top-rated movies and popular TV shows.
  - **movie_info.html**: Displays detailed information about a selected movie, including an option for users to rate it.
  - **tv_info.html**: Similar to movie_info.html but tailored for TV shows, allowing users to select seasons and episodes.

- **static**: This directory holds static files like CSS and JavaScript.
  - **styles.css**: Contains custom styles to enhance the visual appeal of the application.

### Design Choices

While developing the Movie & TV Show Tracker, several design choices were debated:

1. **Framework Choice**: I chose Flask for its simplicity and flexibility. It allows for quick prototyping while being powerful enough to handle the application's requirements.

2. **Database Management**: I opted for SQLAlchemy to manage database interactions due to its ORM capabilities, which simplify data manipulation and enhance code readability.

3. **User Experience**: The decision to implement a rating system was driven by user feedback on similar applications. It provides valuable insights into user preferences and enhances engagement.

4. **Session Management**: I implemented cookie session management to ensure users remain logged in during their session. This feature improves user experience and keeps track of their viewing history seamlessly.

### Conclusion
The Movie & TV Show Tracker serves as a comprehensive tool for users to manage their viewing habits effectively. By leveraging the TMDB API, it provides real-time access to a vast database of movies and TV shows. The project emphasizes user-centric design, ensuring an intuitive interface while delivering robust functionality.

This README.md aims to document the project thoroughly, ensuring that any developer or user can understand its purpose, functionality, and structure. I take pride in this project and look forward to further enhancements based on user feedback and emerging trends in web development.
