
# Yahoo Finance Options Analyzer

This README provides an overview of the structure and features of a yahoo finance analyzer.



## Overview
Developed a dynamic web application for analyzing stock options using Yahoo Finance data, enabling real-time insights and visualizations with Django, Plotly, and Bootstrap. Enhanced users' trading decisions by providing detailed payoff diagrams, trade potentials, and current stock data.



## Technologies Used
* **Django** - Web framework
* **Plotly** - Data visualization
* **Bootstrap** - Front-end framework

## Features
* Real-time stock data retrieval
* Dynamic option legs update
* Payoff diagram visualization
* Trade potentials calculation

## How to use
1. **Clone the repository**: Clone the project repository to your local machine.
    ```bash
    git clone <repository_url>
    ```
2. **Set up a virtual environment**: Create a virtual environment and activate it.
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3. **Install dependencies**: Install dependencies from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```
4. **Apply migrations**: Create the necessary database tables.
    ```bash
    python manage.py migrate
    ```
5. **Run the server**: Start the development server.
    ```bash
    python manage.py runserver
    ```
6. **Access the app**: Open a web browser and navigate to `http://localhost:8000/` to interact with the app.
## App Usage

- **Log in or Sign up**: Use the authentication system to log in or create an account.
- **Analyze Options**: Enter a stock symbol and view real-time data and analysis.
- **View Payoff Diagrams**: Visualize potential gains and losses using dynamic payoff diagrams.
- **Review Trade Potentials**: Understand maximum gains, losses, and breakeven points for informed decision-making.

## Contributing

- Fork the repository.
- Create a new branch (`git checkout -b feature-branch`).
- Make your changes.
- Commit your changes (`git commit -m 'Add new feature'`).
- Push to the branch (`git push origin feature-branch`).
- Create a pull request.


## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For any questions or feedback, please reach out to me at [sharjeel03317840080@03317840080.com].