# DA inputs

La función ***da*** del modulo da.py es la función principal a través de la cual se ejecuta el algoritmo Deferred Acceptance (DA). Esta recibe como argumentos los siguientes archivos:

## Vacancies:
*(type: Dataframe)* Archivo indicando los programas que serán parte del DA. Esta base debe incluir las siguientes columnas:

* **program_id:** Identificador de un programa. Toma valores float o str.
* **quota_id:** Identificador de quota.
* **institution_id:** Identificador de la institución. Genera relaciones entre varios programas.
* **grade_id:** Grado (o nivel) del programa.
* **regular_vacancies:** Cantidad de vacantes de tipo regular.
* **special_i_vacancies:** (Opcional) Cantidad de vacantes de tipo especial. Se espera que i tome valores 1 hasta n, con n la cantidad de vacantes de tipo especial.

Además, cada tupla de (program_id,quota_id) debe ser única.

## Applicants:
*(type:Dataframe)* Archivo indicando a los postulantes al DA. Esta base debe incluir las siguientes columnas:

* **applicant_id:** Identificador de postulante. Toma valores float o str.
* **grade_id:** Grado (o nivel) al que postula.
* **special_assignment:** Int de 0 a n indicando el tipo de asignación, 0 es regular.
* **secured_enrollment_program_id:** (Opcional) En caso de poseer secured enrollment, corresponde a un id de programa. En caso contrario puede tomar valores None o 0.
* **secured_enrollment_quota_id:** (Opcional) En caso de poseer secured enrollment, corresponde a un id de quota. En caso contrario puede tomar valores None o 0.
* **applicant_characteristic_i:**  (Opcional) Columnas con caracteristicas relevantes para alterar el orden de postulacion a quotas.Se espera que i tome valores 1 hasta n, con n la cantidad de caracteristicas.

Además, cada applicant_id debe ser único. Se asume que special assignment se procesa antes en cada grado y en orden 1 a n.

## Applications:
*(type:Dataframe)* Archivo indicando las postulaciones de cada estudiante y la prioridad y lotería de estas. Esta base debe incluir las siguientes columnas:

* **applicant_id:** Corresponde a un id de postulante.
* **program_id:** Corresponde a un id de programa.
* **quota_id:** Corresponde a un id de cuota.
* **institution_id:** Corresponde al id de institución correspondiente al programa.
* **ranking_program:** Lugar de el programa en la postulación del postulante. Toma valores 0 a n con n la cantidad de postulaciones del postulante.
* **priority_profile_program:** Int. Corresponde a un de los perfiles de prioridad del la asignación.
* **priority_number_quota:** Float. Número de prioridad correspondiente al programa y quota de la postulación. Esta determinado por el perfil de prioridad.
* **lottery_number_quota:** (Opcional) Float. Número de lotería correspondiente al programa y quota de la postulación. Si no es ingresado, se llamará al paquete lottery_maker para generar números de lotería. Los parametros para la generación de esta lotería pueden ser entregados como argumentos de la función da.

Para cada estudiante (applicant_id) habrá una fila por cada programa y cuota a las que postula, cuyo orden de postulación está indicado en la columna ranking_program. La columna lottery_number_quota es necesaria, pues el algoritmo DA no genera números de lotería.

## Priority_profiles:
*(type:Dataframe)* Archivo indicando los perfiles de prioridad, indicando además las transiciones de números de prioridad para el caso de sibling dinámico.

* **priority_profile:** Int. Número de prioridad. Se espera tome valores 1 a n, con n la cantidad de perfiles de prioridad.
* **priority_qi:** Prioridad de la quota i. Se espera que i tome valores según la cantidad de cuotas presentes.
* **priority_profile_sibling_transition:** (Opcional) Int. Transición del perfil de prioridad en caso de recibir sibling_priority. Corresponde a uno de los perfiles de prioridad. Es necesario solo en el caso de indicar 'sibling_priority_activation'=True como kwarg.

## Quota_order:
*(type:Dataframe)* Archivo indicando el orden de postulación a las cuotas que le corresponde a distintas combinaciones de perfil de prioridad y características del postulante que no postulan simplemente 1-2-3-4.

* **priority_profile:** Int. Corresponde a uno de los perfiles de prioridad.
* **secured_enrollment_indicator:** (Opcional) Bool. True si el reordenamiento corresponde a un priority profile de secured enrollment. Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **secured_enrollment_quota_id_criteria:** (Opcional) Criterio a cumplir para aplicar el reordenamiento. Toma valores '<','>','>=','<=','==' y '!=' y sus equivalentes verbales ('le','ge','leq','geq','eq' y 'neq'). Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **secured_enrollment_quota_id_value:** (Opcional) Valor a comparar según el criterio anterior. Es necesario solo en el caso de indicar 'secured_enrollment_assignment'=True como kwarg.
* **applicant_characteristic_i_criteria:** (Opcional) Criterio a cumplir para aplicar el reordenamiento. Toma valores '<','>','>=','<=','==' y '!=' y sus equivalentes verbales ('le','ge','leq','geq','eq' y 'neq').
* **applicant_characteristic_i_value:** (Opcional) Valor a comparar según el criterio anterior. Se espera que i tome valores según la cantidad de caracteristicas de los postulantes.
* **order_qj:** Se espera que j tome valores según la cantidad de cuotas de la asignación.

## Siblings
*(type:Dataframe)* Default=None. Archivo indicando las relaciones familiares entre postulantes. Es necesario solo en el caso de indicar 'sibling_priority_activation'=True como kwarg. Esta base debe incluir las siguientes columnas:
* **applicant_id:** Corresponde a un id de postulante.
* **sibling_id:** Corresponde a un id de postulante.

Para cada estudiante (applicant_id) habrá una fila por cada hermana/o (sibling_id). Se espera que cada relación de parentesco esté duplicada, es decir para A y B hermanas/os, tendremos las tuplas (applicant_id=A,sibling_id=B) y (applicant_id=B,sibling_id=A).

## Links
*(type:Dataframe)* Default=None. Archivo indicando las postulaciones en bloque. Es necesario solo en el caso de indicar 'linked_postulation_activation'=True como kwarg. Esta base debe incluir las siguientes columnas:
* **applicant_id:** Corresponde a un id de postulante.
* **linked_id:** Corresponde a un id de postulante.

Para cada estudiante (applicant_id) habrá una fila por cada estudiante en postulación en bloque (linked_id). Se espera que cada relación de postulación familiar esté duplicada, es decir para A y B postulando en bloque, tendremos las tuplas (applicant_id=A, linked_id=B) y (applicant_id=B, linked_id=A).

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
