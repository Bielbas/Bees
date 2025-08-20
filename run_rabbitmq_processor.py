from rabbitmq_processor import RabbitMQBeeProcessor
from rabbitmq_config_docker import RABBITMQ_CONFIG


def main():
    print("RabbitMQ Bee Detection System")
    print("=" * 50)
    
    rabbit_config = RABBITMQ_CONFIG
    print()
    
    processor = RabbitMQBeeProcessor(rabbit_config)
    processor.start_consuming()

if __name__ == "__main__":
    main()
