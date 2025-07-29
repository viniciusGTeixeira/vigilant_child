from .dvr_cftv_analyzer import DvrCFTVAnalyzer
from .ipcam_analyzer import IPCAMAnalyzer
from .webcam_analyzer import WebcamAnalyzer
import cv2

class CameraManager:
    """
    Classe responsável por gerenciar múltiplas fontes de câmera e detectar qual está disponível.
    """
    def __init__(self, dvr_url=None, ipcam_url=None, webcam_index=0):
        """
        Inicializa o gerenciador com as URLs e índice das câmeras.
        """
        self.sources = []
        if dvr_url:
            self.sources.append(DvrCFTVAnalyzer(dvr_url))
        if ipcam_url:
            self.sources.append(IPCAMAnalyzer(ipcam_url))
        self.sources.append(WebcamAnalyzer(webcam_index))
        self.active_source = None

    def detect_and_set_active(self):
        """
        Detecta e define a primeira fonte de câmera disponível.
        """
        for source in self.sources:
            source.open()
            frame = source.get_frame()
            if frame is not None:
                self.active_source = source
                break
            source.release()

    def get_live_frame(self):
        """
        Retorna um frame da fonte ativa. Detecta automaticamente se necessário.
        """
        if self.active_source is None:
            self.detect_and_set_active()
        if self.active_source:
            return self.active_source.get_frame()
        return None

    def release(self):
        """
        Libera o recurso da fonte ativa.
        """
        if self.active_source:
            self.active_source.release()

if __name__ == "__main__":
    # Exemplo de uso
    dvr_url = "rtsp://usuario:senha@ip_do_dvr:porta/canal"  # Substitua pelo seu DVR
    ipcam_url = "rtsp://usuario:senha@ip_da_ipcam:porta/stream"  # Substitua pela sua IP Cam
    webcam_index = 0

    manager = CameraManager(dvr_url, ipcam_url, webcam_index)

    while True:
        frame = manager.get_live_frame()
        if frame is not None:
            cv2.imshow("Ao Vivo - Big Brother CNN", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    manager.release()
    cv2.destroyAllWindows() 