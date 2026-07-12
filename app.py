from db.database import init_db
from ui.main_window import MainWindow


def main():
    # Asegura que la base de datos y tablas estén creadas al iniciar
    init_db()

    # Lanza la interfaz gráfica
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()