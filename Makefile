.PHONY: build run test package clean docker-up docker-down

build:
	./mvnw compile -q

package:
	./mvnw package -DskipTests -q

run: package
	bash ./start.sh

test:
	./mvnw test

clean:
	./mvnw clean -q

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
