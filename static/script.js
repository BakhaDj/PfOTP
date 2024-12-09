window.onload = function () {
    let timeLeft = 30;
    const timerElement = document.getElementById("timer");

    const countdown = setInterval(() => {
        timeLeft--;
        timerElement.textContent = `Осталось: ${timeLeft} секунд`;

        if (timeLeft <= 0) {
            clearInterval(countdown);
            alert("Время вышло!");
            window.location.href = "/login"; // Перенаправление на страницу авторизации
        }
    }, 1000);
};
