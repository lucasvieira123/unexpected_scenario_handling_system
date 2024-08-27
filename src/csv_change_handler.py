# import time
# import os

# def get_line_count(filepath):
#     try:
#         with open(filepath, 'r') as file:
#             return sum(1 for _ in file)
#     except FileNotFoundError:
#         return 0

# def monitor_csv(filepath):
#     last_line_count = get_line_count(filepath)
    
#     while True:
#         time.sleep(0.3)  # Verifica a cada 1 segundo
#         new_line_count = get_line_count(filepath)
        
#         if new_line_count > last_line_count:
#             print("Nova linha adicionada ao CSV!")
#             last_line_count = new_line_count

# if __name__ == "__main__":
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     file_path = os.path.join(script_dir, "collected_telemetry.csv")
    
#     print(f"Monitorando: {file_path}")
#     monitor_csv(file_path)
