<p align="center">
    <img src="logo.png" width="350", height="220">
</p> 
<p align="center">A Fast and Accurate SpellCorrection using Sound and Edit-distance based Correction available in English and Hindi language.      
</p>  
<p align="center">  
  <a href="https://github.com/hellohaptik/spello/stargazers">  
    <img src="https://img.shields.io/github/stars/hellohaptik/spello.svg?colorA=orange&colorB=orange&logo=github"  
         alt="GitHub stars">  
  </a> 
  <a href="https://pepy.tech/project/spello/">  
      <img src="https://pepy.tech/badge/spello" alt="Downloads">  
  </a>   
  <a href="https://pypi.org/project/spello/">  
      <img src="https://img.shields.io/pypi/v/spello?colorB=brightgreen" alt="Pypi package">  
  </a>  
  <a href="https://github.com/hellohaptik/spello/issues">
        <img src="https://img.shields.io/github/issues/hellohaptik/spello.svg"
             alt="GitHub issues">
  </a>
  <a href="https://github.com/hellohaptik/spello/blob/master/LICENSE">  
        <img src="https://img.shields.io/github/license/hellohaptik/spello.svg"  
             alt="GitHub license">  
  </a>
  <a href="https://github.com/hellohaptik/spello/graphs/contributors">  
        <img src="https://img.shields.io/badge/all_contributors-5-blue.svg"  
             alt="Contributors">  
  </a>  
</p>  
  
<p align="center">  
 <a href="#what-is-it">What is it</a> •  
  <a href="#-installation">Installation</a> •  
  <a href="#-️getting-started">Getting Started</a> 
</p>  
</p>

<h2 align="center">What is it</h3>  
  
**Spello** is a spellcorrection model built with combination of two models, <a href="https://en.wikipedia.org/wiki/Soundex">Phoneme</a> and <a href="https://github.com/wolfgarbe/SymSpell"> Symspell</a> Phoneme Model uses Soundex algo in background and suggests correct spellings using phonetic concepts to identify similar sounding words. On the other hand, Symspell Model uses concept of edit-distance in order to suggest correct spellings. Spello get's you best of both, taking into consideration context of the word as well. <br>
Currently, this module is available for **English(en)** and  **Hindi(hi)**.
<h2 align="center">💾 Installation</h2>  
<p align="right"><a href="#what-is-it"><sup>▴ Back to top</sup></a></p>
Install spello via `pip`

```bash  
$ pip install spello
```  
> You can either train a new model from scratch or use pre-trained model. Alternatively you can also train model for your domain and use that on priority while use pre-trained model as a fallback

<h2 align="center">⚡ ️Getting Started</h2> 
<p align="right"><a href="#what-is-it"><sup>▴ Back to top</sup></a></p>
  
#### 1. **Model Initialisation**
Initialise the model for one of the suppored languages. 
```python  
>>> from spello.model import SpellCorrectionModel  
>>> sp = SpellCorrectionModel(language='en')  
```  

#### 2. Model Training - New Model
You can choose to train model by providing data in one of the following format
- List of text or sentences.
- Dict having word and their corresponding count.

**Training providing list of sentences**
```python 
>>> sp.train(['I want to play cricket', 'this is a text corpus'])
```
**Training providing words counter**
```python 
>>> sp.train({'i': 2, 'want': 1, 'play': 1, 'cricket': 10, 'mumbai': 5})
```
> List of text is a recommended type for training data as here model also tries to learn context in which words are appearing, which further help to find best possible suggestion in case more than one suggestions are suggested by symspell or phoneme model

#### 3. Model Prediction
```python  
>>> sp.spell_correct('i wnt to plai kricket')  
{'original_text': 'i wnt to plai kricket',
 'spell_corrected_text': 'i want to play cricket',
 'correction_dict': {'wnt': 'want', 'plai': 'play', 'kricket': 'cricket'}
}
```  

#### 4. Save Model
Call the save method to save the trained model at given model dir 
```python  
>>> sp.save(model_save_dir='/home/ubuntu/')
'/home/ubuntu/model.pkl' # saved model path
```  

#### 5. Load Model 
Load the trained model from saved path, First initialise the model and call the load method
```python  
>>> from spello.model import SpellCorrectionModel
>>> sp = SpellCorrectionModel(language='en')
>>> sp.load('/home/ubuntu/model.pkl')
```  

#### 6. Customize Configuration of Model (Optional)
Here, you are also provided to customize various configuration of the model like 
1. Setting minumum and maximum length eligible for spellcorrection
```python  
>>> sp.config.min_length_for_spellcorrection = 2 # default is 3
>>> sp.config.max_length_for_spellcorrection = 20 # default is 15
```  
2. Setting Max edit distance allowed for each char level for symspell and phoneme model
```python
>>> sp.config.symspell_allowed_distance_map = {2:0, 3: 1, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9:5, 10:5, 11:5, 12:5, 13: 6, 14: 6, 15: 6, 16: 6, 17: 6, 18: 6, 19: 6, 20: 6}
# above dict signifies max edit distance possible for word of length 6 is 3, for length 7 is 4 and so on..
```
*To reset to default config*
```python
>>> sp.set_default_config()
```
there are many more configurations which you can set, check this <a href="https://github.com/hellohaptik/spello/blob/master/spello/config.py">file</a> for more details


## Get Started with Pre-trained Models
We have trained a basic model on 30K news + 30k wikipedia sentences
<br>Follow below steps to get started with these model
1. Download a pretrained model from below links
    
    **language**|**model**|**size**|**md5 hash**
    :-----:|:-----:|:-----:|:-----:
    en|[en.pkl.zip](https://haptik-website-images.haptik.ai/spello\_models/en.pkl.zip)|84M|ec55760a7e25846bafe90b0c9ce9b09f
    en|[en\_large.pkl.zip](https://haptik-website-images.haptik.ai/spello\_models/en\_large.pkl.zip)|284M|9a4f5069b2395c9d5a1e8b9929e0c0a9 
    hi|[hi.pkl.zip](https://haptik-website-images.haptik.ai/spello\_models/hi.pkl.zip)|75M|ad8681161932fdbb8b1368bb16b9644a
    hi|[hi\_large.pkl.zip](https://haptik-website-images.haptik.ai/spello\_models/hi\_large.pkl.zip)|341M|0cc73068f88a73612e7dd84434ad61e6

2. Unzip the downloaded file
3. Init and Load the model by specifying path of unzipped file
```python
>>> from spello.model import SpellCorrectionModel
>>> sp = SpellCorrectionModel(language='en')
>>> sp.load('/path/to/file/en.pkl')
```
4. Run the spell correction
```python
>>> sp.spell_correct('i wnt to ply futbal')
{'original_text': 'i wnt to ply futbal',
 'spell_corrected_text': 'i want to play football',
 'correction_dict': {'wnt': 'want', 'ply': 'play', 'futbal': 'football'}
}

```

To train model for other languages, you can download data from <a href="https://wortschatz.uni-leipzig.de/en/download/">here </a> and follow training process.

## Credits 

This software uses the following open source packages:

- [libindic](https://github.com/libindic/soundex)
- [symspell](https://github.com/wolfgarbe/SymSpell)


## Contribution guidelines
This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

Please read the [contribution guidelines](CONTRIBUTION.md) first.

## Future Scope / Limitations
One of the limitations of the current model is, it does not suggest corrections for any grammatical mistakes or for words in the vocabulary of the model. For example, in a sentence “I want to by Apple”, it will not suggest any correction for “by” as it is a valid English word but the correct replacement should be "buy".

In a future release, we will be adding features to suggest corrections  for improper use word in a sentence.
 


<h2>Citing</h2>
<p align="right"><a href="#what-is-it"><sup>▴ Back to top</sup></a></p>

If you use spello in a scientific publication, we would appreciate references to the following BibTex entry:

```latex
@misc{haptik2020spello,
  title={spello},
  author={Srivastava Aman, Reddy SL Ruthvik },
  howpublished={\url{https://github.com/hellohaptik/spello}},
  year={2020}
}
```
