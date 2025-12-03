"""
Test simple para el endpoint de resumen conversacional.
Prueba con datos de ejemplo sin necesidad de cargar el parquet.
"""
import requests
import json

RESUMEN_ENDPOINT = "http://localhost:8000/api/v1/analysis/resumen"


def test_resumen_simple():
    """Prueba básica con conversación de ejemplo."""
    
    payload = {
        "threadId": "test_thread_001",
        "messages": [
            {
                "id": "msg1",
                "text": "El gobierno ha anunciado una reforma laboral que elimina los lunes festivos del calendario. Esta medida ha generado gran controversia.",
                "createdAt": "2025-06-25T10:00:00Z",
                "author": "NoticiasColombia"
            },
            {
                "id": "msg2",
                "text": "Esto es un ataque directo a los trabajadores! No podemos permitir que nos quiten nuestros derechos. Es hora de protestar!",
                "createdAt": "2025-06-25T10:05:00Z",
                "author": "TrabajadorColombia"
            },
            {
                "id": "msg3",
                "text": "Finalmente una reforma que aumenta la productividad. Los festivos entre semana solo perjudican la economía.",
                "createdAt": "2025-06-25T10:10:00Z",
                "author": "EmpresarioCO"
            },
            {
                "id": "msg4",
                "text": "Esta información es FALSA. He verificado en fuentes oficiales y no existe tal reforma. Cuidado con la desinformación.",
                "createdAt": "2025-06-25T10:15:00Z",
                "author": "FactChecker"
            },
            {
                "id": "msg5",
                "text": "Ya sea cierto o no, el gobierno siempre busca formas de perjudicar al pueblo. Petro tiene que renunciar YA!",
                "createdAt": "2025-06-25T10:20:00Z",
                "author": "OpositoresCO"
            },
            {
                "id": "msg6",
                "text": "Siempre lo mismo... polarización y fake news. Necesitamos verificar antes de opinar con odio.",
                "createdAt": "2025-06-25T10:25:00Z",
                "author": "CiudadanoPensante"
            }
        ]
    }
    
    print("=" * 80)
    print("TEST: Endpoint de Resumen Conversacional")
    print("=" * 80)
    print(f"\nEndpoint: {RESUMEN_ENDPOINT}")
    print(f"Thread ID: {payload['threadId']}")
    print(f"Mensajes a analizar: {len(payload['messages'])}")
    
    print("\nConversación:")
    for msg in payload['messages']:
        print(f"\n  [{msg['author']}]")
        print(f"  {msg['text'][:100]}...")
    
    print(f"\n\nEnviando request al endpoint...")
    
    try:
        response = requests.post(RESUMEN_ENDPOINT, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        print("\n" + "=" * 80)
        print("RESPUESTA EXITOSA")
        print("=" * 80)
        
        print(f"\nThread ID: {data['threadId']}")
        print(f"Mensajes analizados: {data['message_count']}")
        
        print(f"\n" + "─" * 80)
        print("RESUMEN EJECUTIVO")
        print("─" * 80)
        print(data['resumen'])
        
        print(f"\n" + "─" * 80)
        print("TEMAS CLAVE")
        print("─" * 80)
        for i, tema in enumerate(data['temas_clave'], 1):
            print(f"  {i}. {tema}")
        
        print(f"\n" + "─" * 80)
        print("POSTURAS DETECTADAS")
        print("─" * 80)
        for i, postura in enumerate(data['posturas'], 1):
            print(f"  {i}. {postura}")
        
        print(f"\n" + "─" * 80)
        print("TONO EMOCIONAL")
        print("─" * 80)
        print(f"  {data['tono_emocional']}")
        
        print(f"\n" + "─" * 80)
        print("RIESGOS DETECTADOS")
        print("─" * 80)
        if data['riesgos_detectados']:
            for i, riesgo in enumerate(data['riesgos_detectados'], 1):
                print(f"  {i}. {riesgo}")
        else:
            print("  Ningún riesgo detectado")
        
        print(f"\n" + "─" * 80)
        print("CONCLUSIÓN")
        print("─" * 80)
        print(f"  {data['conclusion']}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        
        return True
        
    except requests.exceptions.Timeout:
        print("\nERROR: Timeout al llamar al endpoint (120s)")
        return False
    except requests.exceptions.ConnectionError:
        print("\nERROR: No se pudo conectar al servidor")
        print("   Verifica que el servidor esté corriendo en http://localhost:8000")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\nERROR HTTP: {e}")
        if e.response is not None:
            print(f"\nDetalle del error:")
            try:
                error_data = e.response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(e.response.text)
        return False
    except Exception as e:
        print(f"\nERROR INESPERADO: {str(e)}")
        return False


if __name__ == "__main__":
    print("\nIniciando test del endpoint de resumen...\n")
    success = test_resumen_simple()
    
    if success:
        print("\nEl endpoint de resumen está funcionando correctamente!")
    else:
        print("\nEl test ha fallado. Revisa los errores arriba.")
