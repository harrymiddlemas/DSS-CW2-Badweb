import base64


def hash(x):
    interpolate = len(x)
    new = ""

    for i in range(0, len(x)):

        if x[i].isdigit():
            interpolate += int(x[i])

    for i in range(0, len(x)):
        new += x[i] + str(interpolate)
        interpolate += 1

    # print(new)
    encoded = str(base64.b64encode(new.encode()))

    for x in range(5):
        encoded = str(base64.b64encode(encoded.encode()))
        # print(encoded)

    shuffled = ""

    for x in range(0, len(encoded), 2):

        if x + 1 < len(encoded):
            first = encoded[x]
            second = encoded[x + 1]

            shuffled += second
            shuffled += first

    # print(shuffled)
    hashed = shuffled[0:len(shuffled):round(len(shuffled) / 90)]
    hashed = hashed[80:0:-1]
    print(hashed)

    return hashed


hashes = set(())

hashes.add(hash("possword"))
hashes.add(hash("1111word"))
hashes.add(hash("joffreyy"))
hashes.add(hash("11111111"))
hashes.add(hash("password"))
hashes.add(hash("p4ssword"))
hashes.add(hash("aassword"))
hashes.add(hash("grasword"))
hashes.add(hash("grasworf"))
hashes.add(hash("zzaaaaaaaaaaaaaa"))
hashes.add(hash("aaaaaaaaaaaaaaa"))
hashes.add(hash("aaaaaaaaaaaaaaaa"))
hashes.add(hash("baaaaaaaaaaaaaaa"))
hashes.add(hash("aaaaaaaaaaaaaaab"))
hashes.add(hash("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))

print(len(hashes))

