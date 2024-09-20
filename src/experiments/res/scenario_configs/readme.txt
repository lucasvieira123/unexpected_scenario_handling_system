Temos algumas guidas para preeencher esse json config  


// essa é a configuração em que mudamos contexto da variável e a quantidade de variáveis
{
  "Given": {
    "var_combinations": {
      "battery": [
        "battery >= 10",
        "battery >= 0",
        "battery >= 25",
        "battery >= 50",
        "battery >= 75",
        "battery >= 100",
        "battery <= 10",
        "battery <= 0",
        "battery <= 25",
        "battery <= 50",
        "battery <= 75",
        "battery <= 100"
      ],
      "satellite_count": [
        "satellite_count >= 7",
        "satellite_count >= 0",
        "satellite_count >= 4",
        "satellite_count >= 8",
        "satellite_count >= 12",
        "satellite_count >= 15",
        "satellite_count <= 7",
        "satellite_count >= 0",
        "satellite_count >= 4",
        "satellite_count >= 8",
        "satellite_count >= 12",
        "satellite_count >= 15"
      ],
      "wind_speed": [
        "wind_speed <= 36",
        "wind_speed <= 0",
        "wind_speed <= 90",
        "wind_speed <= 180",
        "wind_speed <= 270",
        "wind_speed <= 360",
        "wind_speed >= 36",
        "wind_speed >= 0",
        "wind_speed >= 90",
        "wind_speed >= 180",
        "wind_speed >= 270",
        "wind_speed >= 360"
      ]
    },
    "is_changeable_number_variables": true, //Se eu deixar true, e não colocar extra_expressions, significa que só vai a quantidade de variáveis importantes (var_combinations)
    // a ideia é que sejam todas variaveis diferentes na expressao extra
    "extra_expressions": [
      "a > 10",
      "b > 10",
      "c > 10",
      "d > 10",
      "e > 10",
      "f > 10"
    ]
  },
  "Then": {
    "var_combinations": {
      "height": [
        "height >= 30",
        "height >= 0",
        "height >= 25",
        "height >= 50",
        "height >= 75",
        "height >= 100",
        "height <= 30",
        "height <= 0",
        "height <= 25",
        "height <= 50",
        "height <= 75",
        "height <= 100"
      ],
      "source_distance": [
        "source_distance == 0",
        "source_distance >= 0",
        "source_distance >= 25",
        "source_distance >= 50",
        "source_distance >= 75",
        "source_distance >= 100",
        "source_distance <= 0",
        "source_distance <= 25",
        "source_distance <= 50",
        "source_distance <= 75",
        "source_distance <= 100"
      ]
    },
    "is_changeable_number_variables": true,
    "extra_expressions": [
      "a > 10",
      "b > 10",
      "c > 10",
      "d > 10",
      "e > 10",
      "f > 10"
    ]
  }
}
