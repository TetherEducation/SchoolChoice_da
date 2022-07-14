# DA inputs

La función ***da*** del modulo da.py es la función principal a través de la cual se ejecuta el algoritmo Deferred Acceptance (DA). Esta recibe como argumentos los siguientes archivos:

## Vacancies:
*(type: Dataframe)* Archivo indicando los programas que serán parte del DA. Esta base debe incluir las siguientes columnas:

* **program_id:** [int,float,str] Identificador de un programa.
* **quota_id:** [int] Identificador de quota.
* **institution_id:** [int,float,str] Identificador de la institución. Genera relaciones entre varios programas.
* **grade_id:** [int] Grado (o nivel) del programa.
* **regular_vacancies:** [int] Cantidad de vacantes de tipo regular.
* **special_i_vacancies:** [int] (Opcional) Cantidad de vacantes de tipo especial. Se espera que i tome valores 1 hasta n, con n la cantidad de vacantes de tipo especial.

Además, cada tupla de (program_id,quota_id) debe ser única.

Ejemplo:

| program_id | quota_id | institution_id | grade_id | regular_vacancies | special_1_vacancies |
| ---------- | -------- | -------------- | -------- | ----------------- | ------------------- |
| 'Program_A' | 1 | 'Institution_A' | 1 | 2 | 0 |
| 'Program_A' | 2 | 'Institution_A' | 1 | 3 | 4 |
| 'Program_B' | 1 | 'Institution_B' | 2 | 5 | 0 |
| 'Program_C' | 2 | 'Institution_A' | 3 | 0 | 1 |
| ... |  |  |  |  |  |


## Applicants:
*(type:Dataframe)* Archivo indicando a los postulantes al DA. Esta base debe incluir las siguientes columnas:

* **applicant_id:** [int,float,str] Identificador de postulante.
* **grade_id:** [int] Grado (o nivel) al que postula.
* **special_assignment:** [int] (Opcional) Int de 0 a n indicando el tipo de asignación, 0 es regular. En caso de no indicar esta columna se asume que todos los postulantes son de tipo regular.
* **secured_enrollment_program_id:** [int,float,str] (Opcional) En caso de poseer secured enrollment, corresponde a un id de programa. En caso contrario puede tomar valores None o 0.
* **secured_enrollment_quota_id:** [int] (Opcional) En caso de poseer secured enrollment, corresponde a un id de quota. En caso contrario puede tomar valores None o 0.
* **applicant_characteristic_i:**  [Any] (Opcional) Columnas con caracteristicas relevantes para alterar el orden de postulacion a quotas.Se espera que i tome valores 1 hasta n, con n la cantidad de caracteristicas. Estas columnas pueden tomar cualquier tipo de valores (ej: int, float, str) siempre y cuando sean consistente con los requisitos expuestos en datafram Quota_order explicado más adelante.

Además, cada applicant_id debe ser único. Se asume que special assignment se procesa antes en cada grado y en orden 1 a n.

Ejemplo:

| applicant_id | grade_id | special_assignment | secured_enrollment_program_id | secured_enrollment_quota_id |
| ------------ | -------- | ------------------ | ----------------------------- | --------------------------- |
| 'Applicant_1' | 1 | 0 | 0 | 0 |
| 'Applicant_2' | 2 | 0 | 'Program_B' | 1 |
| 'Applicant_3' | 1 | 1 | 0 | 0 |
| 'Applicant_4' | 2 | 0 | 0 | 0 |
| ... |  |  |  |  |

## Applications:
*(type:Dataframe)* Archivo indicando las postulaciones de cada estudiante y la prioridad y lotería de estas. Esta base debe incluir las siguientes columnas:

* **applicant_id:** [int,float,str] Corresponde a un id de postulante.
* **program_id:** [int,float,str] Corresponde a un id de programa.
* **quota_id:** [int] Corresponde a un id de cuota.
* **institution_id:** [int,float,str] Corresponde al id de institución correspondiente al programa.
* **ranking_program:** [int] Lugar de el programa en la postulación del postulante. Toma valores 0 a n con n la cantidad de postulaciones del postulante.
* **priority_profile_program:** [int] Corresponde a un de los perfiles de prioridad del la asignación.
* **priority_number_quota:** [int] Número de prioridad correspondiente al programa y quota de la postulación. Esta determinado por el perfil de prioridad.
* **lottery_number_quota:** [float] (Opcional) Número de lotería correspondiente al programa y quota de la postulación. Debe ser un valor entre 0 y 1. Si no es ingresado, se llamará al paquete cb_lottery_maker para generar números de lotería. Los parametros para la generación de esta lotería pueden ser entregados como argumentos de la función da.

Para cada estudiante (applicant_id) habrá una fila por cada programa y cuota a las que postula, cuyo orden de postulación está indicado en la columna ranking_program. La columna lottery_number_quota es necesaria, pues el algoritmo DA no genera números de lotería.

Ejemplo:

| applicant_id | program_id | quota_id | institution_id | ranking_program | priority_profile_program | priority_number_quota | lottery_number_quota |
| ------------ | ---------- | -------- | -------------- | --------------- | ------------------------ | --------------------- | -------------------- |
| 'Applicant_1' | 'Program_A' | 1 | 'Institution_A' | 1 | 3 | 4 | 0.0124 |
| 'Applicant_1' | 'Program_C' | 2 | 'Institution_A' | 2 | 2 | 3 | 0.4592 |
| 'Applicant_1' | 'Program_A' | 2 | 'Institution_A' | 1 | 3 | 3 | 0.3314 |
| 'Applicant_2' | 'Program_B' | 1 | 'Institution_B' | 3 | 1 | 1 | 0.9324 |
| ... |  |  |  |  |  |  |  |

## Priority_profiles:
*(type:Dataframe)* Archivo indicando los perfiles de prioridad, indicando además las transiciones de números de prioridad para el caso de sibling dinámico.

* **priority_profile:** [int] Número de prioridad. Se espera tome valores 1 a n, con n la cantidad de perfiles de prioridad.
* **priority_qi:** [int] Prioridad de la quota i. Se espera que i tome valores según la cantidad de cuotas presentes.
* **priority_profile_sibling_transition:** [int] (Opcional) Transición del perfil de prioridad en caso de recibir sibling_priority. Corresponde a uno de los perfiles de prioridad. Es necesario solo en el caso de indicar 'sibling_priority_activation'=True como kwarg.

Ejemplo:

| priority_profile | priority_q1 | priority_q2 | priority_profile_sibling_transition |
| ------------ | -------- | ------------------ | ----------------------------- |
| 1 | 3 | 3 | 5 |
| 2 | 3 | 2 | 3 |
| 3 | 1 | 2 | 3 |
| 4 | 2 | 2 | 5 |
| ... |  |  |  |

## Quota_order:
*(type:Dataframe)* Archivo indicando el orden de postulación a las cuotas que le corresponde a distintas de perfiles de prioridad. El orden de postulaciones puede tambien depender del secured enrollment del estudiante y de caracteristicas del estudiante indicadas como 'applicant_characteristic_i' en la base de applicants. Se asume que los postulantes postulan a las cuotas en orden ascendente (1-2-3-...), salvo en los casos particulares indicados en este DataFrame.

* **priority_profile:** [int] Corresponde a uno de los perfiles de prioridad.
* **secured_enrollment_indicator:** (Opcional) Bool. True si el reordenamiento corresponde a un priority profile de secured enrollment. Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **secured_enrollment_quota_id_criteria:** (Opcional) Criterio a cumplir para aplicar el reordenamiento. Toma valores '<','>','>=','<=','==' y '!=' y sus equivalentes verbales ('le','ge','leq','geq','eq' y 'neq'). Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **secured_enrollment_quota_id_value:** (Opcional) Valor a comparar según el criterio anterior. Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **applicant_characteristic_i_criteria:** (Opcional) Criterio a cumplir para aplicar el reordenamiento. Toma valores '<','>','>=','<=','==' y '!=' y sus equivalentes verbales ('le','ge','leq','geq','eq' y 'neq').
* **applicant_characteristic_i_value:** (Opcional) Valor a comparar según el criterio anterior. Se espera que i tome valores según la cantidad de caracteristicas de los postulantes.
* **order_qj:** Se espera que j tome valores según la cantidad de cuotas de la asignación.

Ejemplo:

| priority_profile | secured_enrollment_indicator | secured_enrollment_quota_id_criteria | secured_enrollment_quota_id_value | order_q1 | order_q2 |
| ------------ | -------- | ------------------ | ----------------------------- | --- | --- |
| 1 | False | '' | 0 | 2 | 1 |
| 2 | False | '' | 0 | 2 | 1 |
| 2 | True | '>=' | 2 | 2 | 1 |
| 3 | False | '' | 0 | 2 | 1 |
| ... |  |  |  |

## Siblings
*(type:Dataframe)* Default=None. Archivo indicando las relaciones familiares entre postulantes. Es necesario solo en el caso de indicar 'sibling_priority_activation'=True como kwarg. Esta base debe incluir las siguientes columnas:
* **applicant_id:** Corresponde a un id de postulante.
* **sibling_id:** Corresponde a un id de postulante.

Para cada estudiante (applicant_id) habrá una fila por cada hermana/o (sibling_id). Se espera que cada relación de parentesco esté duplicada, es decir para A y B hermanas/os, tendremos las tuplas (applicant_id=A,sibling_id=B) y (applicant_id=B,sibling_id=A).

Ejemplo:

| applicant_id | sibling_id |
| ------------ | ---------- |
| 'Applicant_1' | 'Applicant_2' |
| 'Applicant_2' | 'Applicant_1' |
| 'Applicant_5' | 'Applicant_83' |
| 'Applicant_83' | 'Applicant_5' |
| ... |  |

## Links
*(type:Dataframe)* Default=None. Archivo indicando las postulaciones en bloque. Es necesario solo en el caso de indicar 'linked_postulation_activation'=True como kwarg. Esta base debe incluir las siguientes columnas:
* **applicant_id:** Corresponde a un id de postulante.
* **linked_id:** Corresponde a un id de postulante.

Para cada estudiante (applicant_id) habrá una fila por cada estudiante en postulación en bloque (linked_id). Se espera que cada relación de postulación familiar esté duplicada, es decir para A y B postulando en bloque, tendremos las tuplas (applicant_id=A, linked_id=B) y (applicant_id=B, linked_id=A).

Ejemplo:

| applicant_id | linked_id |
| ------------ | ---------- |
| 'Applicant_1' | 'Applicant_2' |
| 'Applicant_2' | 'Applicant_1' |
| 'Applicant_7' | 'Applicant_22' |
| 'Applicant_22' | 'Applicant_7' |
| ... |  |

## Optional arguments
Además de lo anterior, la función da puede recibir los siguientes keyword arguments opcionales:
* **order:** {'descending', 'ascending'}. Default='descending'. Orden en el que se corre el algoritmo.
* **sibling_priority_activation:** Bool. Default=False. Activa prioridad de hermano entre niveles y tipos de asignación.
* **linked_postulation_activation:** Bool. Default=False. Activa postulación en bloque.
* **secured_enrollment_assignment:** Bool. Default=False. Activa el uso de secured enrollment.
* **forced_secured_enrollment_assignment:** Bool. Default=False. Fuerza el uso de secured enrollment en caso de programas sin vacantes.
* **transfer_capacity_activation:** Bool. Default=False. Activa la transferencia de cupos entre tipos de asignación.
* **check_inputs:** Bool. Default=True. Revisa ciertos campos necesarios en los inputs con el fin de prevenir errores.
* **kwargs** Parametros asociados a la generación de números de lotería mediante el paquete complementario lottery_maker. Estos parametros son considerados solo en el caso que el dataframe de Applications no posea la columna 'lottery_number_quota'. Lea la documentación de lottery_maker para más detalles de los posibles parámetros.
